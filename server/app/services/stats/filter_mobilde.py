# app/services/stats/filters/filter_mobilde.py
from app.models.car import ListingMobileDe, TechnicalDetails, Equipment
from app.schemas.stats.analytics import AvgPriceByBrand, ListingSchema, TechnicalDetailsSchema, EquipmentSchema


def filtered_listings(filters: ListingSchema) -> list[ListingMobileDe]:
    """
    Get car listings filtered by the ListingFilter schema criteria.
    """
    conditions = [ListingMobileDe.is_active.is_(True)]

    if filters.brand:
        conditions.append(ListingMobileDe.brand.ilike(f"%{filters.brand}%"))
    if filters.model:
        conditions.append(ListingMobileDe.model.ilike(f"%{filters.model}%"))
    if filters.registration_year:
        conditions.append(ListingMobileDe.registration_year == filters.registration_year)
    if filters.mileage:
        conditions.append(ListingMobileDe.mileage <= filters.mileage)
    if filters.city_or_postal_code:
        conditions.append(ListingMobileDe.city_or_postal_code.ilike(f"%{filters.city_or_postal_code}%"))
    if filters.color:
        conditions.append(ListingMobileDe.color.ilike(f"%{filters.color}%"))
    if filters.price_lte:
        conditions.append(ListingMobileDe.price <= filters.price_lte)
    if filters.price_gte:
        conditions.append(ListingMobileDe.price >= filters.price_gte)
    return conditions


def filtered_tech_details(filters: TechnicalDetailsSchema) -> list[TechnicalDetails]:
    """
    Get technical details filtered by the TechnicalDetailsSchema criteria.
    """
    conditions = []

    if filters.damage_condition:
        conditions.append(TechnicalDetails.damage_condition.ilike(f"%{filters.damage_condition}%"))
    if filters.category:
        conditions.append(TechnicalDetails.category.ilike(f"%{filters.category}%"))
    if filters.trim_line:
        conditions.append(TechnicalDetails.trim_line.ilike(f"%{filters.trim_line}%"))
    if filters.sku:
        conditions.append(TechnicalDetails.sku.ilike(f"%{filters.sku}%"))
    if filters.country_version:
        conditions.append(TechnicalDetails.country_version.ilike(f"%{filters.country_version}%"))
    if filters.power:
        conditions.append(TechnicalDetails.power == filters.power)
    if filters.engine_type:
        conditions.append(TechnicalDetails.engine_type.ilike(f"%{filters.engine_type}%"))
    if filters.other_energy_source:
        conditions.append(TechnicalDetails.other_energy_source.ilike(f"%{filters.other_energy_source}%"))
    if filters.battery:
        conditions.append(TechnicalDetails.battery.ilike(f"%{filters.battery}%"))
    if filters.battery_capacity:
        conditions.append(TechnicalDetails.battery_capacity == filters.battery_capacity)
    if filters.battery_certificate:
        conditions.append(TechnicalDetails.battery_certificate.ilike(f"{filters.battery_capacity}"))
    if filters.battery_range:
        conditions.append(TechnicalDetails.battery_range == filters.battery_range)
    if filters.num_seats:
        conditions.append(TechnicalDetails.num_seats == filters.num_seats)
    if filters.door_count:
        conditions.append(TechnicalDetails.door_count == filters.door_count)
    if filters.transmission:
        conditions.append(TechnicalDetails.transmission.ilike(f"%{filters.transmission}%"))
    if filters.emissions_sticker:
        conditions.append(TechnicalDetails.emissions_sticker.ilike(f"%{filters.emissions_sticker}%"))
    if filters.first_year_registration:
        conditions.append(TechnicalDetails.first_year_registration == filters.first_year_registration)
    if filters.first_month_registration:
        conditions.append(TechnicalDetails.first_month_registration == filters.first_month_registration)
    if filters.number_of_previous_owners:
        conditions.append(TechnicalDetails.number_of_previous_owners.ilike(f"%{filters.number_of_previous_owners}%"))
    if filters.hu_year:
        conditions.append(TechnicalDetails.hu_year == filters.hu_year)
    if filters.hu_month:
        conditions.append(TechnicalDetails.hu_month == filters.hu_month)
    if filters.climatisation:
        conditions.append(TechnicalDetails.climatisation.ilike(f"%{filters.climatisation}%"))
    if filters.park_assists:
        conditions.append(TechnicalDetails.park_assists.ilike(f"%{filters.park_assists}%"))
    if filters.airbags:
        conditions.append(TechnicalDetails.airbags.ilike(f"%{filters.airbags}%"))
    if filters.manufacturer_color_name:
        conditions.append(TechnicalDetails.manufacturer_color_name.ilike(f"%{filters.manufacturer_color_name}%"))
    if filters.interior:
        conditions.append(TechnicalDetails.interior.ilike(f"%{filters.interior}%"))
    if filters.trailer_load_braked:
        conditions.append(TechnicalDetails.trailer_load_braked == filters.trailer_load_braked)
    if filters.trailer_load_unbraked:
        conditions.append(TechnicalDetails.trailer_load_unbraked == filters.trailer_load_unbraked)
    if filters.net_weight:
        conditions.append(TechnicalDetails.net_weight == filters.net_weight)
    if filters.waranty_registration:
        conditions.append(TechnicalDetails.waranty_registration == filters.waranty_registration)
    return conditions


def filtered_equipment(filters: EquipmentSchema) -> list[Equipment]:
    """"
    Get equipment filtered by the EquipmentSchema criteria.
    """
    conditions = []  # List to hold filter conditions
    filter_data = filters.dict(exclude_unset=True)  # Convert schema to dictionary and exclude unset fields
    for field_name, value in filter_data.items():  # Iterate over each field and value in the filter data
        if value is not None:
            equipment_field = getattr(Equipment, field_name, None)  # Get the field from the Equipment model
            if equipment_field is not None:  # Check if the field exists in the Equipment model
                conditions.append(equipment_field == value)
    return conditions
