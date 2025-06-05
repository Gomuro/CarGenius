import time
import random
import logging
import re
import os
import json
from datetime import datetime
from typing import List, Callable, Any, Optional
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from src.utils.bot.bot_humanity import random_sleep
from src.database import SessionLocal, Subscription, User
from src.GLOBAL import GLOBAL
from sqlalchemy.orm.exc import ObjectDeletedError


logger = logging.getLogger(__name__)


def save_follow_statistics(account_id: int, count: int) -> None:
    """Save follow count statistics to a file."""
    stats_path = GLOBAL.PATH.STATISTIC_PATH
    if not os.path.exists(stats_path):
        os.makedirs(stats_path)
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    stats_file = os.path.join(stats_path, f'{account_id}.{date_str}.json')
    try:
        with open(stats_file, 'w') as f:
            json.dump({'follow_count': count, 'last_updated': datetime.now().isoformat()}, f)
        print(f"Saved statistics: {count} follows")
    except Exception as e:
        print(f"Error saving statistics: {e}")


def get_follow_statistics(account_id: int) -> int:
    """Get the current follow count for today from statistics file."""
    stats_path = GLOBAL.PATH.STATISTIC_PATH
    date_str = datetime.now().strftime("%Y-%m-%d")
    stats_file = os.path.join(stats_path, f'{account_id}.{date_str}.json')
    
    follow_count = 0
    try:
        if os.path.exists(stats_file):
            with open(stats_file, 'r') as f:
                data = json.load(f)
                follow_count = data.get('follow_count', 0)
            print(f"Loaded statistics for account {account_id}: {follow_count} follows")
        else:
            print(f"No statistics file found for today, starting from 0")
    except Exception as e:
        print(f"Error loading statistics: {e}")
    
    return follow_count


def process_users_with_pattern(
    driver, 
    users: List[User], 
    account_id: int, 
    group_id: Optional[int] = None,
    max_follows_per_launch: int = 500,
    max_follow_per_day: int = 500,
    max_followers_on_account_to_subscribe: int = 300,
    proxy_change_callback: Optional[Callable[[], Any]] = None,
    follow_count: int = 0,
    _running: bool = True
) -> tuple[int, bool]:
    """
    Process users following a specific pattern:
    - Follow 1 person
    - Wait 7 seconds
    - Subscribe to another person
    - After 10 people, pause for 2 minutes
    - After 50 people, pause for 30 minutes
    - Change IP through proxy
    - Repeat

    Args:
        driver: Selenium driver instance
        users: List of User objects to process
        account_id: Current account ID
        group_id: Group ID for subscription tracking (optional)
        max_follows_per_launch: Maximum number of users to follow in one process
        max_follow_per_day: Maximum number of follows per day
        max_followers_on_account_to_subscribe: Skip users with more followers than this
        proxy_change_callback: Callback function to change proxy IP
        follow_count: Current follow count (will be updated from statistics)
        _running: Boolean flag to control execution

    Returns:
        tuple: (updated follow count, running status)
    """
    # Import here to avoid circular dependency
    from src.start_manager import StartManager, AccountState
    
    if not users:
        logger.warning("No users provided to process")
        return follow_count, False
    
    # Get today's follow count from statistics first, overriding the passed parameter
    # This ensures we're using the most up-to-date count from disk
    follow_count = get_follow_statistics(account_id)
    
    # Check if we've already hit the daily limit
    if follow_count >= max_follow_per_day:
        logger.warning(f"Already reached daily follow limit of {max_follow_per_day}")
        start_manager = StartManager.get_instance()
        launch_id = f"account_{account_id}"
        start_manager.set_status(launch_id, AccountState.COMPLETED, 
                                f"Daily follow limit reached: {follow_count}/{max_follow_per_day}")
        return follow_count, False
    
    # Calculate how many more follows we can do today
    remaining_follows_today = max_follow_per_day - follow_count
    
    # Adjust max_follows_per_launch if needed to not exceed daily limit
    effective_max_follows = min(max_follows_per_launch, remaining_follows_today)
    logger.info(f"Account {account_id}: {follow_count} follows so far today, " 
                f"will follow up to {effective_max_follows} more users")
    
    session = SessionLocal()
    try:
        # Get fresh user IDs from the database instead of using passed objects
        user_ids = [user.id for user in users]
        
        # Create a new batch of users from the database using their IDs
        users_batch = []
        for user_id in user_ids:
            try:
                user = session.query(User).get(user_id)
                if user:
                    users_batch.append(user)
            except Exception as e:
                print(f"Error loading user {user_id}: {e}")
        
        if not users_batch:
            logger.warning("No valid users found in database")
            start_manager = StartManager.get_instance()
            launch_id = f"account_{account_id}"
            start_manager.set_status(launch_id, AccountState.ERROR, "No valid users found in database")
            return follow_count, False
            
        pattern_counter = 0
        batch_counter = 0
        start_manager = StartManager.get_instance()
        launch_id = f"account_{account_id}"
        
        # Update status to working
        start_manager.set_status(launch_id, AccountState.WORKING, 
                               f"Processing users with pattern - {follow_count}/{max_follow_per_day} follows today")
        
        count_follow_on_this_launch = 0
        while users_batch and _running and count_follow_on_this_launch < effective_max_follows:
            # Current number of subscriptions considering all processes
            current_total = get_follow_statistics(account_id)
            if current_total >= max_follow_per_day:
                logger.warning(f"🛑 Daily limit {max_follow_per_day} already reached")
                break

            # Process one user
            try:
                # Get a random user from the batch
                user_index = random.randrange(len(users_batch))
                user = users_batch.pop(user_index)
                
                # Make sure we have a valid user object with URL
                if not hasattr(user, 'url') or not user.url:
                    print(f"Invalid user object (missing URL), skipping")
                    continue
                
                # Navigate to user profile
                driver.get(user.url)
                time.sleep(5)
                
                try:
                    # Get followers count first
                    try:
                        followers_count = driver.find_element(By.XPATH, 
                            "//a[@data-testid='profileHeaderFollowersButton']//span[1]").text
                        
                        # Convert K/M/B to actual numbers
                        try:
                            followers_count = re.sub(r'([0-9.]+)([KMB])', lambda x: '{:.0f}'.format(
                                float(x.group(1)) * {'K': 1e3, 'M': 1e6, 'B': 1e9}[x.group(2)]),
                                followers_count)
                        except Exception as e:
                            print(f"Failed to parse followers count for {user.url}: {e}")
                            try:
                                # Delete user by ID to avoid persistence issues
                                session.query(User).filter_by(id=user.id).delete()
                                session.commit()
                            except Exception as e:
                                if 'database is locked' in str(e):
                                    print(f"Error: {e}. Skipping.")
                                    continue
                                    
                            # Get new user to replace this one
                            try:
                                new_users = session.query(User).all()
                                if new_users:
                                    new_user = random.choice(new_users)
                                    if new_user not in users_batch:
                                        users_batch.append(new_user)
                            except Exception as e:
                                print(f"Error getting replacement user: {e}")
                            continue
                            
                        print(f"Processing user {user.url} with {followers_count} followers...")
                        
                        # Skip users with too many followers
                        if int(followers_count) >= max_followers_on_account_to_subscribe:
                            print(f"Skipping user with {followers_count} followers (limit: {max_followers_on_account_to_subscribe})")
                            try:
                                # Delete user by ID to avoid persistence issues
                                session.query(User).filter_by(id=user.id).delete()
                                session.commit()
                            except Exception as e:
                                if 'database is locked' in str(e):
                                    print(f"Error: {e}. Skipping.")
                                    continue
                                    
                            # Get new user to replace this one
                            try:
                                new_users = session.query(User).all()
                                if new_users:
                                    new_user = random.choice(new_users)
                                    if new_user not in users_batch:
                                        users_batch.append(new_user)
                            except Exception as e:
                                print(f"Error getting replacement user: {e}")
                            continue
                    except NoSuchElementException:
                        print(f"Could not find followers count for {user.url}")
                    
                    # Try to find and click follow button
                    follow_btn = driver.find_element(By.XPATH, "//button[@data-testid='followBtn']")
                    
                    # Record subscription in database if group_id is provided
                    if group_id:
                        existing_sub = session.query(Subscription).filter_by(
                            user_id=user.id, 
                            group_id=group_id
                        ).first()
                        
                        if not existing_sub:
                            # try to click follow button
                            try:
                                follow_btn.click()
                                random_sleep(7, 10)  # Wait 7 seconds as per pattern
                                new_sub = Subscription(user_id=user.id, group_id=group_id)
                                session.add(new_sub)
                                session.commit()
                                
                                # Increment counters
                                follow_count += 1
                                count_follow_on_this_launch += 1
                                pattern_counter += 1
                                batch_counter += 1
                                
                                # Save statistics - does a write to disk on every follow
                                save_follow_statistics(account_id, follow_count)
                                
                                logger.info(f"Followed user {user.url} ({count_follow_on_this_launch}/{effective_max_follows}, total: {follow_count}/{max_follow_per_day})")
                                
                                # Update status with progress
                                start_manager.set_status(launch_id, AccountState.WORKING, 
                                                      f"Following users: {count_follow_on_this_launch}/{effective_max_follows} (Total: {follow_count}/{max_follow_per_day})")
                                
                                # Check if we've hit our daily limit
                                if follow_count >= max_follow_per_day:
                                    logger.info(f"Reached daily follow limit of {max_follow_per_day}")
                                    start_manager.set_status(launch_id, AccountState.COMPLETED, 
                                                           f"Daily follow limit reached: {follow_count}/{max_follow_per_day}")
                                    return follow_count, False
                                
                            except Exception as e:
                                # Try to click with js
                                try:
                                    driver.execute_script("arguments[0].click();", follow_btn)
                                    random_sleep(7, 10)  # Wait 7 seconds as per pattern
                                    new_sub = Subscription(user_id=user.id, group_id=group_id)
                                    session.add(new_sub)
                                    session.commit()
                                    
                                    # Increment counters
                                    follow_count += 1
                                    count_follow_on_this_launch += 1
                                    pattern_counter += 1
                                    batch_counter += 1
                                    
                                    # Save statistics
                                    save_follow_statistics(account_id, follow_count)
                                    
                                    logger.info(f"Followed user {user.url} ({count_follow_on_this_launch}/{effective_max_follows}, total: {follow_count}/{max_follow_per_day})")
                                    
                                    # Update status with progress
                                    start_manager.set_status(launch_id, AccountState.WORKING, 
                                                          f"Following users: {count_follow_on_this_launch}/{effective_max_follows} (Total: {follow_count}/{max_follow_per_day})")
                                    
                                    # Check if we've hit our daily limit
                                    if follow_count >= max_follow_per_day:
                                        logger.info(f"Reached daily follow limit of {max_follow_per_day}")
                                        start_manager.set_status(launch_id, AccountState.COMPLETED, 
                                                               f"Daily follow limit reached: {follow_count}/{max_follow_per_day}")
                                        return follow_count, False
                                    
                                except Exception as e:
                                    logger.error(f"Error in clicking follow button: {e}")
                                    start_manager.set_status(launch_id, AccountState.ERROR, f"Error clicking follow button: {e}")
                                    _running = False
                                return follow_count, _running
                
                    # Check for pattern thresholds
                    if pattern_counter >= 10:
                        logger.info("Reached 10 follows, pausing for 2 minutes")
                        start_manager.set_status(launch_id, AccountState.WORKING, f"Pausing for 2 minutes after 10 follows")
                        pattern_counter = 0
                        print("Pausing for 2 minutes")
                        time.sleep(120)  # 2 minutes
                        print("Resuming pattern. 2 minutes passed.")
                    
                    if batch_counter >= 50:
                        logger.info("Reached 50 subscriptions - pause for 30 minutes")
                        
                        # Save statistics
                        save_follow_statistics(account_id, follow_count)
                        
                        # Change IP through proxy
                        if proxy_change_callback:
                            logger.info("Changing IP through proxy")
                            proxy_change_callback()

                        # Fix the time of the pause end
                        resume_time = time.time() + 1800  # 30 minutes
                        
                        # Wait until resume_time
                        while time.time() < resume_time:
                            time.sleep(5)  # Check every 5 seconds
                            
                            # Break if process is stopped
                            if not _running:
                                return follow_count, False
                        
                        logger.info("Continuing work after pause")
                        batch_counter = 0  # Reset the counter
                
                except NoSuchElementException:
                    # Check if already following
                    try:
                        driver.find_element(By.XPATH, "//button[@data-testid='unfollowBtn']")
                        logger.info(f"Already following user {user.url}")
                    except NoSuchElementException:
                        logger.warning(f"Failed to process user: {user.url}")
                
            except ObjectDeletedError:
                print(f"User object was deleted from database, skipping")
                continue
            except Exception as e:
                print(f"Error processing user: {e}")
                continue
            
            # If we're running out of users, get more
            if len(users_batch) < 50:
                try:
                    # Create a new session to ensure fresh database state
                    temp_session = SessionLocal()
                    try:
                        # Get fresh users from the database
                        if group_id:
                            # Get users not already subscribed to
                            subscribed_user_ids = [sub.user_id for sub in 
                                temp_session.query(Subscription.user_id).filter_by(group_id=group_id).all()]
                            fresh_users = temp_session.query(User).filter(~User.id.in_(subscribed_user_ids)).all()
                        else:
                            fresh_users = temp_session.query(User).all()
                            
                        # Add users not already in batch
                        batch_user_ids = [u.id for u in users_batch]
                        new_users = [u for u in fresh_users if u.id not in batch_user_ids]
                        
                        if new_users:
                            # Take a sample of new users to add
                            sample_size = min(50, len(new_users))
                            sampled_users = random.sample(new_users, sample_size)
                            
                            # Add these users to our main session
                            for new_user in sampled_users:
                                user_from_main_session = session.query(User).get(new_user.id)
                                if user_from_main_session:
                                    users_batch.append(user_from_main_session)
                    finally:
                        temp_session.close()
                except Exception as e:
                    print(f"Error refreshing user batch: {e}")
            
            # After successful subscription
            follow_count += 1
            current_total = get_follow_statistics(account_id) + 1
            if current_total >= max_follow_per_day:
                logger.info("🔴 Reached maximum daily limit!")
                save_follow_statistics(account_id, current_total)
                break
            
            # Save the updated value
            save_follow_statistics(account_id, current_total)
        
        # Final save of statistics
        save_follow_statistics(account_id, follow_count)
        
        # Check why we stopped
        if follow_count >= max_follow_per_day:
            start_manager.set_status(launch_id, AccountState.COMPLETED, f"Reached maximum follows per day: {follow_count}/{max_follow_per_day}")
        elif count_follow_on_this_launch >= effective_max_follows:
            start_manager.set_status(launch_id, AccountState.COMPLETED, f"Reached maximum follows for this launch: {count_follow_on_this_launch}/{effective_max_follows}")
        elif not _running:
            start_manager.set_status(launch_id, AccountState.COMPLETED, "Process stopped")
        elif not users_batch:
            start_manager.set_status(launch_id, AccountState.COMPLETED, "Ran out of users to process")
        else:
            start_manager.set_status(launch_id, AccountState.COMPLETED, f"Finished processing with {count_follow_on_this_launch} follows in this launch (total: {follow_count}/{max_follow_per_day})")
        
        return follow_count, _running
    
    except Exception as e:
        logger.error(f"Error in processing users with pattern: {e}")
        launch_id = f"account_{account_id}"
        start_manager = StartManager.get_instance()
        start_manager.set_status(launch_id, AccountState.ERROR, f"Error: {str(e)}")
        return follow_count, False
    
    finally:
        # Final save before exiting
        if follow_count > 0:
            save_follow_statistics(account_id, follow_count)
        session.close() 