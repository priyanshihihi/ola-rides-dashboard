"""
Synthetic Ola-style ride-hailing dataset generator
Generates: Bookings, Customers, Drivers, Reviews (linked via IDs)
~8000 bookings, realistic patterns including cancellations and fake-looking reviews
"""

import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker('en_IN')
Faker.seed(42)
random.seed(42)
np.random.seed(42)

# ---------- CONFIG ----------
N_BOOKINGS = 8000
N_CUSTOMERS = 1800
N_DRIVERS = 350
CITIES = ['Bengaluru', 'Mumbai', 'Delhi', 'Hyderabad', 'Pune', 'Chennai']
VEHICLE_TYPES = ['Mini', 'Sedan', 'Auto', 'Bike', 'Prime SUV']
PAYMENT_METHODS = ['UPI', 'Credit Card', 'Cash', 'Ola Money', 'Debit Card']
CANCEL_REASONS_CUSTOMER = ['Found alternate ride', 'Driver took too long', 'Changed plans', 'Price too high', 'App issue']
CANCEL_REASONS_DRIVER = ['Customer not reachable', 'Long pickup distance', 'Vehicle issue', 'Personal emergency']

START_DATE = datetime(2025, 1, 1)
END_DATE = datetime(2025, 12, 31)

def random_date(start, end):
    delta = end - start
    random_days = random.randint(0, delta.days)
    random_seconds = random.randint(0, 86399)
    return start + timedelta(days=random_days, seconds=random_seconds)

# ---------- CUSTOMERS ----------
customers = []
for i in range(1, N_CUSTOMERS + 1):
    signup = random_date(START_DATE - timedelta(days=400), END_DATE - timedelta(days=30))
    customers.append({
        'customer_id': f'CUST{i:05d}',
        'name': fake.name(),
        'city': random.choice(CITIES),
        'signup_date': signup.strftime('%Y-%m-%d'),
        'email': fake.email(),
    })
customers_df = pd.DataFrame(customers)

# ---------- DRIVERS ----------
drivers = []
for i in range(1, N_DRIVERS + 1):
    join = random_date(START_DATE - timedelta(days=600), END_DATE - timedelta(days=30))
    # Most drivers are decent, a small % are "problem drivers" (lower ratings, more cancellations)
    is_problem_driver = random.random() < 0.08
    base_rating = round(random.uniform(3.0, 4.2), 2) if is_problem_driver else round(random.uniform(4.2, 5.0), 2)
    drivers.append({
        'driver_id': f'DRV{i:04d}',
        'name': fake.name(),
        'vehicle_type': random.choice(VEHICLE_TYPES),
        'city': random.choice(CITIES),
        'join_date': join.strftime('%Y-%m-%d'),
        'driver_rating_avg': base_rating,
        'is_problem_driver_flag': is_problem_driver  # hidden ground-truth, useful later to validate your AI feature
    })
drivers_df = pd.DataFrame(drivers)

# ---------- BOOKINGS ----------
bookings = []
booking_status_weights = [0.78, 0.12, 0.07, 0.03]  # Completed, Cancelled by Customer, Cancelled by Driver, No Driver Found
statuses = ['Completed', 'Cancelled by Customer', 'Cancelled by Driver', 'No Driver Found']

for i in range(1, N_BOOKINGS + 1):
    cust = customers_df.sample(1).iloc[0]
    drv = drivers_df.sample(1).iloc[0]
    pickup_dt = random_date(START_DATE, END_DATE)
    distance = round(np.random.gamma(2.2, 2.5), 1)
    distance = max(0.8, min(distance, 45))
    vehicle = drv['vehicle_type']
    base_rate = {'Bike': 6, 'Auto': 9, 'Mini': 11, 'Sedan': 14, 'Prime SUV': 19}[vehicle]
    fare = round(distance * base_rate + random.uniform(10, 40), 2)
    status = random.choices(statuses, weights=booking_status_weights)[0]

    cancel_reason = None
    if status == 'Cancelled by Customer':
        cancel_reason = random.choice(CANCEL_REASONS_CUSTOMER)
    elif status == 'Cancelled by Driver':
        cancel_reason = random.choice(CANCEL_REASONS_DRIVER)

    bookings.append({
        'booking_id': f'BK{i:06d}',
        'customer_id': cust['customer_id'],
        'driver_id': drv['driver_id'],
        'city': cust['city'],
        'pickup_datetime': pickup_dt.strftime('%Y-%m-%d %H:%M:%S'),
        'vehicle_type': vehicle,
        'distance_km': distance,
        'fare': fare if status == 'Completed' else 0,
        'payment_method': random.choice(PAYMENT_METHODS) if status == 'Completed' else None,
        'booking_status': status,
        'cancellation_reason': cancel_reason,
    })

bookings_df = pd.DataFrame(bookings)

# ---------- REVIEWS ----------
# Only completed rides get reviews, and not all of them (typical ~55% leave a review)
genuine_templates = [
    "Driver {name} was very polite and the {vehicle} was clean. Reached on time despite traffic near {city}.",
    "Smooth ride, driver took the flyover route which saved time. Would book again.",
    "AC wasn't working properly but driver was courteous. Fare was reasonable for {distance}km.",
    "Driver was a bit late by 10 mins but called ahead to inform. Drive was safe and smooth.",
    "Good experience overall, vehicle was in good condition. Driver knew the {city} routes well.",
    "Decent ride but the driver took a longer route than necessary, added to the fare.",
    "Excellent service, driver helped with my luggage and was very professional.",
    "Average ride, nothing special but no complaints either. On time pickup.",
]

# Suspicious/fake patterns: generic, repeated, mismatched sentiment, spammy
suspicious_templates = [
    "nice", "good service", "ok ok", "best app best driver", "good good good",
    "Amazing super excellent service best in class wow!!!",
    "Visit www.bestdeals-ride.com for discount codes!!!",
    "Call 9876543210 for direct booking and skip the app fees",
    "nice nice nice nice nice",
    "Best driver ever! Best driver ever! Best driver ever!",
]

reviews = []
review_id = 1
completed_bookings = bookings_df[bookings_df['booking_status'] == 'Completed']

for _, b in completed_bookings.iterrows():
    if random.random() > 0.55:
        continue  # no review left

    drv_row = drivers_df[drivers_df['driver_id'] == b['driver_id']].iloc[0]
    # Problem drivers are more likely to have suspicious/manipulated reviews (inflated 5-stars to offset bad ones)
    make_suspicious = random.random() < (0.35 if drv_row['is_problem_driver_flag'] else 0.06)

    if make_suspicious:
        text = random.choice(suspicious_templates)
        # Suspicious reviews often have mismatched high ratings to mask real reputation
        star = random.choices([5, 4, 1], weights=[0.6, 0.2, 0.2])[0]
    else:
        template = random.choice(genuine_templates)
        text = template.format(
            name=fake.first_name(),
            vehicle=b['vehicle_type'],
            city=b['city'],
            distance=b['distance_km']
        )
        # Genuine reviews have sentiment-consistent ratings
        if 'wasn\'t working' in text or 'longer route' in text or 'Average' in text:
            star = random.choices([3, 4], weights=[0.6, 0.4])[0]
        elif 'bit late' in text:
            star = random.choices([3, 4], weights=[0.5, 0.5])[0]
        else:
            star = random.choices([4, 5], weights=[0.4, 0.6])[0]

    review_date = (datetime.strptime(b['pickup_datetime'], '%Y-%m-%d %H:%M:%S') + timedelta(hours=random.randint(1, 48)))

    reviews.append({
        'review_id': f'REV{review_id:06d}',
        'booking_id': b['booking_id'],
        'customer_id': b['customer_id'],
        'driver_id': b['driver_id'],
        'review_text': text,
        'star_rating': star,
        'review_date': review_date.strftime('%Y-%m-%d %H:%M:%S'),
    })
    review_id += 1

reviews_df = pd.DataFrame(reviews)

# ---------- SAVE ----------
import os
os.makedirs('/home/claude/ola_data', exist_ok=True)
customers_df.to_csv('/home/claude/ola_data/customers.csv', index=False)
drivers_df.drop(columns=['is_problem_driver_flag']).to_csv('/home/claude/ola_data/drivers.csv', index=False)  # hide ground truth from main dataset
drivers_df.to_csv('/home/claude/ola_data/drivers_with_groundtruth.csv', index=False)  # keep for your own validation
bookings_df.to_csv('/home/claude/ola_data/bookings.csv', index=False)
reviews_df.to_csv('/home/claude/ola_data/reviews.csv', index=False)

print(f"Customers: {len(customers_df)}")
print(f"Drivers: {len(drivers_df)}")
print(f"Bookings: {len(bookings_df)}")
print(f"Reviews: {len(reviews_df)}")
print(f"Suspicious-looking reviews seeded: {reviews_df['review_text'].isin(suspicious_templates).sum()} (approx, some genuine text overlaps)")
