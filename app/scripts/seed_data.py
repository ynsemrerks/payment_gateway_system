"""Seed database with test data."""
import sys
from decimal import Decimal
from app.database import SessionLocal
from app.models.user import User
from app.utils.security import generate_api_key


def seed_data():
    """Seed database with test users."""
    db = SessionLocal()
    
    try:
        # Check if users already exist
        existing_users = db.query(User).count()
        if existing_users > 0:
            print(f"Database already has {existing_users} users. Skipping seed.")
            return
        
        # Create test users
        test_users = [
            {
                "email": "alice@example.com",
                "balance": Decimal("1000.00")
            },
            {
                "email": "bob@example.com",
                "balance": Decimal("500.00")
            },
            {
                "email": "charlie@example.com",
                "balance": Decimal("0.00")
            }
        ]
        
        created_users = []
        for user_data in test_users:
            api_key = generate_api_key()
            user = User(
                email=user_data["email"],
                api_key=api_key,
                balance=user_data["balance"]
            )
            db.add(user)
            created_users.append({
                "email": user_data["email"],
                "api_key": api_key,
                "balance": user_data["balance"]
            })
        
        db.commit()
        
        print("✅ Database seeded successfully!")
        print("\n📝 Test Users Created:")
        print("-" * 80)
        for user in created_users:
            print(f"Email: {user['email']}")
            print(f"API Key: {user['api_key']}")
            print(f"Balance: ${user['balance']}")
            print("-" * 80)
        
    except Exception as e:
        print(f"❌ Error seeding database: {str(e)}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
