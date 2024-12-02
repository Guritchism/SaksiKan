from app import app, db, User, Show, Schedule
import os
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

def setup_database():
    with app.app_context():
        # Drop all tables if they exist
        db.drop_all()
        print("Dropped all existing tables")

        # Create all tables with new schema
        db.create_all()
        print("Created new tables with updated schema")

        # Create admin user
        admin = User(
            username='admin',
            email='admin@saksikan.com',
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        print("Created admin user")

        # Create sample show
        show = Show(
            title='Pertunjukan Contoh',
            description='Ini adalah pertunjukan contoh untuk testing',
            production='Produksi Contoh',
            location='Teater Utama'
        )
        db.session.add(show)
        db.session.commit()
        print("Created sample show")

        # Create sample schedules
        today = datetime.now()
        for i in range(3):
            schedule_date = today + timedelta(days=i+1)
            schedule = Schedule(
                show_id=show.id,
                date=schedule_date,
                available_seats=100,
                price=150000,
                is_active=True
            )
            db.session.add(schedule)
        
        db.session.commit()
        print("Created sample schedules")
        print("\nDatabase setup completed successfully!")

if __name__ == '__main__':
    setup_database()
