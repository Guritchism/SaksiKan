from app import app, db, Show, Schedule
from datetime import datetime, timedelta

def init_db():
    with app.app_context():
        # Create tables
        db.create_all()

        # Sample shows from Teater Koma
        shows = [
            {
                'title': 'Sie Jin Kwie',
                'production': 'Teater Koma',
                'description': 'Kisah Sie Jin Kwie, seorang prajurit yang setia dan pemberani dalam melawan ketidakadilan.',
                'poster_path': '/static/img/sie-jin-kwie.jpeg',
                'location': 'Graha Bhakti Budaya - TIM Jakarta',
                'schedules': [
                    {
                        'date': datetime.now() + timedelta(days=7),
                        'available_tickets': 100,
                        'price': 150000
                    },
                    {
                        'date': datetime.now() + timedelta(days=8),
                        'available_tickets': 100,
                        'price': 150000
                    }
                ]
            },
            {
                'title': 'Sampek Engtay',
                'production': 'Teater Koma',
                'description': 'Adaptasi cerita cinta klasik Tiongkok yang mengharukan tentang Sampek dan Engtay.',
                'poster_path': '/static/img/sampek-engtay.jpg',
                'location': 'Graha Bhakti Budaya - TIM Jakarta',
                'schedules': [
                    {
                        'date': datetime.now() + timedelta(days=14),
                        'available_tickets': 100,
                        'price': 175000
                    },
                    {
                        'date': datetime.now() + timedelta(days=15),
                        'available_tickets': 100,
                        'price': 175000
                    }
                ]
            }
        ]

        # Add shows to database
        for show_data in shows:
            schedules_data = show_data.pop('schedules')
            show = Show(**show_data)
            db.session.add(show)
            db.session.flush()  # To get the show.id

            # Add schedules for the show
            for schedule_data in schedules_data:
                schedule = Schedule(show_id=show.id, **schedule_data)
                db.session.add(schedule)

        db.session.commit()

if __name__ == '__main__':
    init_db()
