import os
import json
import urllib.error
import urllib.request
from urllib import response
import uuid
from flask import Flask, request, session, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
# import psycopg2 (Removed - switching to Supabase Client for HTTP compatibility)
# import psycopg2.extras
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta, datetime
from supabase import create_client, Client

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.permanent_session_lifetime = timedelta(minutes=60)
app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,
)

CORS(
    app,
    supports_credentials=True,
    origins=["http://localhost:3000", "http://127.0.0.1:3000"],
)

# ==============================
# SUPABASE CLIENT (for Storage)
# ==============================
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

STORAGE_BUCKET = "property-images"
USER_TABLE = "users"

def create_auth_user(email, password):
    if not SUPABASE_SERVICE_ROLE_KEY:
        auth_response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        return auth_response.user.id

    url = f"{os.getenv('SUPABASE_URL')}/auth/v1/admin/users"
    payload = json.dumps({
        "email": email,
        "password": password,
        "email_confirm": True
    }).encode("utf-8")
    request_obj = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request_obj, timeout=15) as auth_result:
            auth_user = json.loads(auth_result.read().decode("utf-8"))
            return auth_user["id"]
    except urllib.error.HTTPError as err:
        error_body = err.read().decode("utf-8")
        raise Exception(error_body or str(err)) from err

def find_user_profile(**filters):
    query = supabase.table(USER_TABLE).select("*")
    for column_name, value in filters.items():
        query = query.eq(column_name, value)
    response = query.limit(1).execute()
    return response.data[0] if response.data else None

def save_user_profile(user_data):
    # Always use auth_id for upsert if available - it's the only guaranteed unique identifier
    if user_data.get("auth_id"):
        # Check if auth_id already exists
        existing_profile = find_user_profile(auth_id=user_data["auth_id"])
        if existing_profile:
            # Update using auth_id (unique constraint)
            supabase.table(USER_TABLE).update(user_data).eq("auth_id", user_data["auth_id"]).execute()
        else:
            # Insert new profile
            supabase.table(USER_TABLE).insert(user_data).execute()
    else:
        # Fallback if no auth_id (shouldn't happen in normal flow)
        supabase.table(USER_TABLE).insert(user_data).execute()

def update_user_profile_by_email(email, update_data):
    # Get the user by email
    response = supabase.table(USER_TABLE).select("*").eq("email", email).execute()
    if response.data:
        # Update using the id (primary key) to avoid constraint issues
        user_id = response.data[0].get("id")
        if user_id:
            update_response = supabase.table(USER_TABLE).update(update_data).eq("id", user_id).execute()
            return update_response.data[0] if update_response.data else response.data[0]
    return None

@app.route('/api/test_supabase')
def test_supabase():
    try:
        response = supabase.table('properties').select("*").execute()       
        return jsonify({
            "status": "success",
            "message": "Supabase Connection OK",
            "count": response.count
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
# ==============================
# DATABASE UTILITY (Removed legacy psycopg2 connection)
# ==============================
# All DB operations now use the 'supabase' client defined above.


# ==============================
# CORE CLASSES FROM CLASS DIAGRAM
# ==============================
class User:
    def __init__(self, user_id=None, name=None, email=None, role=None):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.role = role

    @staticmethod
    def register(name, email, password, role, phone_number):
        email = (email or "").strip().lower()
        role = (role or "user").strip().lower()
        if role not in ("admin", "user"):
            return jsonify({"status": "error", "message": "Invalid role"}), 400

        try:
            existing_profile = find_user_profile(email=email)
            if existing_profile:
                return jsonify({
                    "status": "error",
                    "message": "Account already exists. Please sign in."
                }), 409
        except Exception as err:
            return jsonify({"status": "error", "message": str(err)}), 500

        try:
            user_auth_id = create_auth_user(email, password)

        except Exception as e:
            error_msg = str(e).lower()
            if "already" in error_msg or "registered" in error_msg:
                try:
                    login_res = supabase.auth.sign_in_with_password({
                        "email": email,
                        "password": password
                    })
                    user_auth_id = login_res.user.id
                except Exception as login_err:
                    return jsonify({"status": "error", "message": str(login_err)}), 400
            elif "rate limit" in error_msg or "rate_limit" in error_msg:
                return jsonify({
                    "status": "error",
                    "message": "Supabase email rate limit exceeded. Wait a few minutes or use an already-created account to sign in."
                }), 429
            else:
                return jsonify({"status": "error", "message": str(e)}), 400

        # ✅ INSERT INTO CORRECT TABLE
        try:
            user_data = {
                "name": name,
                "email": email,
                "role": role,
                "phone_number": phone_number,
                "auth_id": user_auth_id
            }

            print("INSERTING USER:", user_data)  # debug

            save_user_profile(user_data)

            return jsonify({
                "status": "success",
                "message": "Account created successfully! Please log in."
            })

        except Exception as err:
            error_msg = str(err).lower()
            if "duplicate" in error_msg or "unique" in error_msg:
                return jsonify({
                    "status": "error",
                    "message": "Account already exists. Please sign in."
                }), 409
            return jsonify({"status": "error", "message": str(err)}), 400

    @staticmethod
    def login(email, password, role):
        email = (email or "").strip().lower()
        role = (role or "user").strip().lower()
        if role not in ("admin", "user"):
            return jsonify({"status": "error", "message": "Invalid role"}), 400

        try:
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            user_auth_id = auth_response.user.id

        except Exception:
            return jsonify({
                "status": "error",
                "message": "Invalid credentials"
            }), 401

        # ✅ FETCH FROM CORRECT TABLE
        try:
            user_data = find_user_profile(auth_id=user_auth_id, role=role)
            if not user_data:
                email_profile = find_user_profile(email=email)
                if email_profile:
                    if email_profile.get("role") != role:
                        return jsonify({
                            "status": "error",
                            "message": f"Please login as {email_profile.get('role', 'the registered role')}."
                        }), 401
                    user_data = update_user_profile_by_email(email, {"auth_id": user_auth_id}) or email_profile
                    user_data["auth_id"] = user_auth_id
                else:
                    fallback_name = email.split("@")[0] if email else "User"
                    save_user_profile({
                        "name": fallback_name,
                        "email": email,
                        "role": role,
                        "phone_number": "",
                        "auth_id": user_auth_id
                    })
                    user_data = find_user_profile(auth_id=user_auth_id, role=role)

        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

        if user_data:
            db_user_id = user_data.get('id') or user_data.get('user_id')
            if not db_user_id:
                return jsonify({
                    "status": "error",
                    "message": "User profile is missing a primary key"
                }), 500
            user_data['id'] = db_user_id

            session.permanent = True
            session['logged_in'] = True
            session['user_id'] = db_user_id
            session['user_id'] = user_data['id']   # ✅ FIXED (not user_id column)
            session['user_id'] = db_user_id
            session['name'] = user_data['name']
            session['role'] = user_data['role']

            return jsonify({
                "status": "success",
                "message": "Logged in successfully",
                "role": user_data['role'],
                "name": user_data['name'],
                "user_id": db_user_id
            })
        else:
            existing_auth_profile = find_user_profile(auth_id=user_auth_id)
            if existing_auth_profile:
                return jsonify({
                    "status": "error",
                    "message": f"Please login as {existing_auth_profile.get('role', 'the registered role')}."
                }), 401
            return jsonify({
                "status": "error",
                "message": "User not found in DB"
            }), 401

    @staticmethod
    def logout():
        session.clear()
        try:
            supabase.auth.sign_out()
        except:
            pass
        return jsonify({
            "status": "success",
            "message": "Logged out"
        })

class Admin(User):
    def __init__(self, user_id, name, email, role):
        super().__init__(user_id, name, email, role)

    def addProperty(self, address, city, state, country, description, image_url, image_description):
        try:
            property_data = {
                "owner_id": self.user_id,
                "address": address,
                "city": city,
                "state": state,
                "country": country,
                "description": description,
                "image_url": image_url,
                "image_description": image_description
            }
            response = supabase.table('properties').insert(property_data).execute()
            if not response.data:
                return jsonify({"status": "error", "message": "Failed to add property"}), 400
            property_id = response.data[0]['property_id']
            return jsonify({"status": "success", "message": "Property added successfully!", "property_id": property_id})
        except Exception as err:
            return jsonify({"status": "error", "message": str(err)}), 400

    def editProperty(self, property_id, address, city, state, country, description, image_url, image_description):
        try:
            update_data = {
                "address": address,
                "city": city,
                "state": state,
                "country": country,
                "description": description,
                "image_url": image_url,
                "image_description": image_description
            }
            response = supabase.table('properties')\
                .update(update_data)\
                .eq("property_id", property_id)\
                .eq("owner_id", self.user_id)\
                .execute()
            return jsonify({"status": "success", "message": "Property updated successfully!"})
        except Exception as err:
            return jsonify({"status": "error", "message": str(err)}), 400

    def deleteProperty(self, property_id):
        try:
            # Note: We perform deletes sequentially as Supabase client doesn't 
            # support multi-table transactions in one call easily.
            # In production, RLS or DB Triggers would handle cascading deletes.
            supabase.table('rooms').delete().eq("property_id", property_id).execute()
            supabase.table('amenities').delete().eq("property_id", property_id).execute()
            response = supabase.table('properties')\
                .delete()\
                .eq("property_id", property_id)\
                .eq("owner_id", self.user_id)\
                .execute()
            
            if not response.data:
                return jsonify({"status": "error", "message": "Property not found or no permission."}), 403
            return jsonify({"status": "success", "message": "Property deleted successfully!"})
        except Exception as err:
            return jsonify({"status": "error", "message": str(err)}), 400

    def viewDashboard(self):
        try:
            response = supabase.table('properties').select("*").eq("owner_id", self.user_id).execute()
            properties = response.data
            return jsonify({"properties": properties, "name": self.name, "role": self.role})
        except Exception as err:
            return jsonify({"status": "error", "message": str(err)}), 400

    @staticmethod
    def addAmenity(property_id, name, description):
        try:
            amenity_data = {"property_id": property_id, "name": name, "description": description}
            supabase.table('amenities').insert(amenity_data).execute()
            return jsonify({"status": "success", "message": "Amenity added successfully!"})
        except Exception as err:
            print("DEBUG: Add amenity error:", err)
            return jsonify({"status": "error", "message": str(err)}), 400

    @staticmethod
    def viewAmenities(property_id):
        try:
            response = supabase.table('amenities').select("*").eq("property_id", property_id).execute()
            return response.data
        except Exception:
            return []

    @staticmethod
    def deleteAmenity(amenity_id, property_id):
        try:
            supabase.table('amenities').delete().eq("amenity_id", amenity_id).execute()
            return jsonify({"status": "success", "message": "Amenity deleted successfully!"})
        except Exception as err:
            return jsonify({"status": "error", "message": str(err)}), 400

    @staticmethod
    def editAmenity(amenity_id, name, description, property_id):
        try:
            update_data = {"name": name, "description": description}
            supabase.table('amenities').update(update_data).eq("amenity_id", amenity_id).execute()
            return jsonify({"status": "success", "message": "Amenity updated successfully!"})
        except Exception as err:
            return jsonify({"status": "error", "message": str(err)}), 400
        return property_id

    @staticmethod
    def addRoom(property_id, room_type, capacity, price_per_night, availability_status):
        try:
            room_data = {
                "property_id": property_id,
                "room_type": room_type,
                "capacity": int(capacity),
                "price_per_night": float(price_per_night),
                "availability_status": bool(availability_status)
            }
            supabase.table('rooms').insert(room_data).execute()
            return jsonify({"status": "success", "message": "Room added successfully!"})
        except Exception as err:
            return jsonify({"status": "error", "message": str(err)}), 400

    @staticmethod
    def viewRooms(property_id):
        try:
            response = supabase.table('rooms').select("*").eq("property_id", property_id).execute()
            return response.data
        except Exception:
            return []

    @staticmethod
    def deleteRoom(room_id, property_id):
        try:
            supabase.table('rooms').delete().eq("room_id", room_id).execute()
            return jsonify({"status": "success", "message": "Room deleted successfully!"})
        except Exception as err:
            return jsonify({"status": "error", "message": str(err)}), 400

    @staticmethod
    def editRoom(room_id, room_type, capacity, price_per_night, availability_status, property_id):
        try:
            update_data = {
                "room_type": room_type,
                "capacity": int(capacity),
                "price_per_night": float(price_per_night),
                "availability_status": bool(availability_status)
            }
            supabase.table('rooms').update(update_data).eq("room_id", room_id).execute()
            return jsonify({"status": "success", "message": "Room updated successfully!"})
        except Exception as err:
            return jsonify({"status": "error", "message": str(err)}), 400
        return property_id

    @staticmethod
    def getRoomStatus(property_id, owner_id):
        try:
            # 1. Fetch property details
            p_res = supabase.table('properties').select("*").eq("property_id", property_id).eq("owner_id", owner_id).execute()
            if not p_res.data:
                return None, None
            property_details = p_res.data[0]

            # 2. Fetch rooms
            r_res = supabase.table('rooms').select("*").eq("property_id", property_id).execute()
            rooms = r_res.data

            # 3. Fetch active bookings (for room status)
            today = datetime.now().date().isoformat()
            # Find bookings where current date is between check_in and check_out
            b_res = supabase.table('bookings'
)\
                .select("room_id")\
                .lte("check_in_date", today)\
                .gt("check_out_date", today)\
                .execute()
            booked_room_ids = {b['room_id'] for b in b_res.data}

            for room in rooms:
                room['is_booked'] = room['room_id'] in booked_room_ids

            return property_details, rooms
        except Exception:
            return None, None
            


class Guest(User):
    def __init__(self, user_id, name, email, role):
        super().__init__(user_id, name, email, role)

    def searchRooms(self):
        try:
            response = supabase.table('properties').select("*").execute()
            return jsonify({"properties": response.data, "name": self.name, "role": self.role})
        except Exception:
            return jsonify({"properties": [], "name": self.name, "role": self.role})

    def bookRoom(self, room_id, property_id, check_in_date, check_out_date, payment_method):
        try:
            # 1. Fetch room details
            res = supabase.table('rooms').select("*").eq("room_id", room_id).single().execute()
            room = res.data
            if not room or not bool(room['availability_status']):
                return jsonify({"status": "error", "message": "This room is currently turned off by the admin."}), 400

            check_in = datetime.strptime(check_in_date, '%Y-%m-%d')
            check_out = datetime.strptime(check_out_date, '%Y-%m-%d')
            num_days = (check_out - check_in).days
            if num_days <= 0:
                return jsonify({"status": "error", "message": "Invalid date range."}), 400

            # 2. Check for overlaps
            # Overlap logic: existing.check_in < new.check_out AND existing.check_out > new.check_in
            bookings_res = supabase.table('bookings'
)\
                .select("booking_id")\
                .eq("room_id", room_id)\
                .lt("check_in_date", check_out_date)\
                .gt("check_out_date", check_in_date)\
                .execute()
            
            if bookings_res.data:
                return jsonify({"status": "error", "message": "Room is already booked for these dates."}), 400

            total_price = num_days * float(room['price_per_night'])

            # 3. Create booking
            booking_data = {
                "user_id": self.user_id,
                "room_id": room_id,
                "check_in_date": check_in_date,
                "check_out_date": check_out_date,
                "total_price": total_price,
            }
            b_res = supabase.table('bookings'
).insert(booking_data).execute()
            booking_id = b_res.data[0]['booking_id']

            # 4. Create payment
            payment_data = {
                "booking_id": booking_id,
                "payment_method": payment_method,
                "amount": total_price,
                "payment_status": 'completed',
                "payment_date": datetime.now().isoformat()
            }
            supabase.table('payments').insert(payment_data).execute()

            return jsonify({"status": "success", "message": "Booking and payment successful!", "booking_id": booking_id})
        except Exception as err:
            return jsonify({"status": "error", "message": str(err)}), 400

    def cancelBooking(self, booking_id):
        try:
            # 1. Verify access
            res = supabase.table('bookings'
).select("*").eq("booking_id", booking_id).eq("user_id", self.user_id).execute()
            if not res.data:
                return jsonify({"status": "error", "message": "Booking not found or no permission."}), 404

            # 2. Delete related records
            supabase.table('payments').delete().eq("booking_id", booking_id).execute()
            supabase.table('bookings'
).delete().eq("booking_id", booking_id).execute()
            return jsonify({"status": "success", "message": "Booking cancelled successfully."})
        except Exception as err:
            return jsonify({"status": "error", "message": str(err)}), 400

    def viewBookings(self):
        try:
            res = supabase.table('bookings')\
                .select("*")\
                .eq("user_id", self.user_id)\
                .execute()

            room_ids = list({b['room_id'] for b in res.data if b.get('room_id')})
            rooms_by_id = {}
            properties_by_id = {}

            if room_ids:
                rooms_res = supabase.table('rooms')\
                    .select("*")\
                    .in_("room_id", room_ids)\
                    .execute()
                rooms_by_id = {r['room_id']: r for r in rooms_res.data}

                property_ids = list({r['property_id'] for r in rooms_res.data if r.get('property_id')})
                if property_ids:
                    properties_res = supabase.table('properties')\
                        .select("*")\
                        .in_("property_id", property_ids)\
                        .execute()
                    properties_by_id = {p['property_id']: p for p in properties_res.data}

            result = []
            for b in res.data:
                room = rooms_by_id.get(b.get('room_id'), {})
                prop = properties_by_id.get(room.get('property_id'), {})
                bd = {
                    "booking_id": b['booking_id'],
                    "check_in_date": b['check_in_date'],
                    "check_out_date": b['check_out_date'],
                    "total_price": b['total_price'],
                    "room_type": room.get('room_type'),
                    "address": prop.get('address')
                }
                result.append(bd)
            return jsonify({"bookings": result})
        except Exception as err:
            return jsonify({"bookings": [], "error": str(err)})

    @staticmethod
    def viewPropertyDetails(property_id):
        try:
            p_res = supabase.table('properties')\
                .select("*")\
                .eq("property_id", property_id)\
                .single().execute()

            p_data = p_res.data
            amenities_res = supabase.table('amenities')\
                .select("*")\
                .eq("property_id", property_id)\
                .execute()
            rooms_res = supabase.table('rooms')\
                .select("*")\
                .eq("property_id", property_id)\
                .execute()

            amenities = amenities_res.data or []
            rooms = rooms_res.data or []
            room_ids = [r['room_id'] for r in rooms]
            room_reviews = {str(rid): [] for rid in room_ids}

            if room_ids:
                try:
                    rev_res = supabase.table('reviews')\
                        .select("*")\
                        .in_("room_id", room_ids)\
                        .order("created_at", desc=True)\
                        .execute()
                except Exception as err:
                    print(f"Reviews unavailable: {err}")
                    rev_res = None
            else:
                rev_res = None

            user_ids = list({rev['user_id'] for rev in (rev_res.data if rev_res else []) if rev.get('user_id')})
            users_by_id = {}
            if user_ids:
                users_res = supabase.table('users')\
                    .select("user_id,name")\
                    .in_("user_id", user_ids)\
                    .execute()
                users_by_id = {u['user_id']: u.get('name', 'Unknown User') for u in users_res.data}

            if not rev_res:
                return p_data, amenities, rooms, room_reviews

            for rev in rev_res.data:
                r_id = str(rev['room_id'])
                rev_formatted = {
                    "rating": rev['rating'],
                    "comment": rev['comment'],
                    "user_name": users_by_id.get(rev.get('user_id'), 'Unknown User'),
                    "created_at": rev['created_at']
                }
                if r_id in room_reviews:
                    room_reviews[r_id].append(rev_formatted)

            return p_data, amenities, rooms, room_reviews
        except Exception as e:
            print(f"Error in viewPropertyDetails: {e}")
            return None, [], [], {}

    @staticmethod
    def addReview(room_id, user_id, rating, comment, property_id):
        try:
            review_data = {
                "room_id": room_id,
                "user_id": user_id,
                "rating": int(rating),
                "comment": comment
            }
            supabase.table('reviews').insert(review_data).execute()
            return jsonify({"status": "success", "message": "Your review has been added."})
        except Exception as err:
            return jsonify({"status": "error", "message": "An error occurred. Please try again."}), 400


class Scheduler:
    @staticmethod
    def updateRoomAvailability():
        try:
            today = datetime.now().date().isoformat()
            # Fetch bookings that have ended
            res = supabase.table('bookings'
).select("room_id").lte("check_out_date", today).execute()
            expired_room_ids = {b['room_id'] for b in res.data}
            
            if expired_room_ids:
                # Update room availability status
                for rid in expired_room_ids:
                    supabase.table('rooms').update({"availability_status": True}).eq("room_id", rid).execute()
                print(f"Updated availability for {len(expired_room_ids)} room(s).")
        except Exception as err:
            print(f"Error updating room availability: {err}")


# ==============================
# API ROUTES
# ==============================

@app.route('/api/me')
def me():
    if 'logged_in' not in session:
        return jsonify({"logged_in": False}), 401
    return jsonify({
        "logged_in": True,
        "user_id": session['user_id'],
        "name": session['name'],
        "role": session['role']
    })

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    return User.register(
        data['name'], data['email'], data['password'],
        data['role'], data['phone_number']
    )

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    return User.login(data['email'], data['password'], data['role'])

@app.route('/api/logout', methods=['POST'])
def logout():
    return User.logout()

@app.route('/api/dashboard')
def dashboard():
    if 'logged_in' not in session or session['role'] != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    admin = Admin(session['user_id'], session['name'], None, 'admin')
    return admin.viewDashboard()

@app.route('/api/user_dashboard')
def user_dashboard():
    if 'logged_in' not in session or session['role'] != 'user':
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    guest = Guest(session['user_id'], session['name'], None, 'user')
    return guest.searchRooms()

@app.route('/api/book_room/<int:room_id>/<int:property_id>', methods=['GET', 'POST'])
def book_room(room_id, property_id):
    if 'logged_in' not in session or session['role'] != 'user':
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    if request.method == 'POST':
        data = request.get_json()
        guest = Guest(session['user_id'], session['name'], None, 'user')
        return guest.bookRoom(
            room_id, property_id,
            data['check_in_date'], data['check_out_date'], data['payment_method']
        )

    try:
        res = supabase.table('rooms').select("*").eq("room_id", room_id).single().execute()
        room = res.data
        return jsonify({"room": room, "property_id": property_id})
    except Exception:
        return jsonify({"room": None, "property_id": property_id})

@app.route('/api/room_status/<int:property_id>')
def room_status(property_id):
    if 'logged_in' not in session or session['role'] != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    property_details, rooms = Admin.getRoomStatus(property_id, session['user_id'])
    if not property_details:
        return jsonify({"status": "error", "message": "Property not found."}), 404
    return jsonify({"property": property_details, "rooms": rooms})

@app.route('/api/view_more/<int:property_id>')
def view_more(property_id):
    if 'logged_in' not in session or session['role'] != 'user':
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    property_details, amenities, rooms, room_reviews = Guest.viewPropertyDetails(property_id)
    return jsonify({
        "property": property_details,
        "amenities": amenities,
        "rooms": rooms,
        "room_reviews": room_reviews
    })

@app.route('/api/add_review/<int:room_id>', methods=['POST'])
def add_review(room_id):
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    data = request.get_json()
    return Guest.addReview(
        room_id, session['user_id'],
        int(data['rating']), data['comment'], data.get('property_id')
    )

@app.route('/api/my_bookings')
def my_bookings():
    if 'logged_in' not in session or session['role'] != 'user':
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    guest = Guest(session['user_id'], session['name'], None, 'user')
    return guest.viewBookings()

@app.route('/api/cancel_booking/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    if 'logged_in' not in session or session['role'] != 'user':
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    guest = Guest(session['user_id'], session['name'], None, 'user')
    return guest.cancelBooking(booking_id)

@app.route('/api/delete_property/<int:property_id>', methods=['DELETE'])
def delete_property(property_id):
    if 'logged_in' not in session or session['role'] != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    admin = Admin(session['user_id'], session['name'], None, 'admin')
    return admin.deleteProperty(property_id)

@app.route('/api/upload_property_image', methods=['POST'])
def upload_property_image():
    """Upload a property image to Supabase Storage and return the public URL."""
    if 'logged_in' not in session or session['role'] != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    if 'image' not in request.files:
        return jsonify({"status": "error", "message": "No image file provided"}), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({"status": "error", "message": "Empty filename"}), 400

    # Determine extension and build a unique storage path
    ext = os.path.splitext(image_file.filename)[1].lower() or '.jpg'
    file_name = f"{uuid.uuid4()}{ext}"
    file_bytes = image_file.read()
    content_type = image_file.content_type or 'image/jpeg'

    try:
        # Upload to Supabase Storage
        supabase.storage.from_(STORAGE_BUCKET).upload(
            path=file_name,
            file=file_bytes,
            file_options={"content-type": content_type}
        )
        # Build public URL
        public_url = f"{os.getenv('SUPABASE_URL')}/storage/v1/object/public/{STORAGE_BUCKET}/{file_name}"
        return jsonify({"status": "success", "image_url": public_url})
    except Exception as err:
        print(f"DEBUG: Image upload error: {str(err)}")
        return jsonify({"status": "error", "message": str(err)}), 500

@app.route('/api/add_property', methods=['POST'])
def add_property():
    if 'logged_in' not in session or session['role'] != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    data = request.get_json()
    admin = Admin(session['user_id'], session['name'], None, 'admin')
    return admin.addProperty(
        data['address'], data['city'], data['state'], data['country'],
        data['description'], data.get('image_url', ''), data.get('image_description', '')
    )

@app.route('/api/edit_property/<int:property_id>', methods=['GET', 'PUT'])
def edit_property(property_id):
    if 'logged_in' not in session or session['role'] != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    if request.method == 'PUT':
        data = request.get_json()
        admin = Admin(session['user_id'], session['name'], None, 'admin')
        return admin.editProperty(
            property_id,
            data['address'], data['city'], data['state'], data['country'],
            data['description'], data.get('image_url', ''), data.get('image_description', '')
        )
    try:
        res = supabase.table('properties')\
            .select("*")\
            .eq("property_id", property_id)\
            .eq("owner_id", session['user_id'])\
            .single().execute()
        return jsonify({"property": res.data})
    except Exception:
        return jsonify({"property": None})

@app.route('/api/view_amenities/<int:property_id>')
def view_amenities(property_id):
    if 'logged_in' not in session or session['role'] != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    amenities = Admin.viewAmenities(property_id)
    return jsonify({"amenities": amenities, "property_id": property_id})

@app.route('/api/add_amenities/<int:property_id>', methods=['POST'])
def add_amenities(property_id):
    if 'logged_in' not in session or session['role'] != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    data = request.get_json()
    return Admin.addAmenity(property_id, data['amenity_name'], data['amenity_description'])

@app.route('/api/delete_amenity/<int:amenity_id>', methods=['DELETE'])
def delete_amenity(amenity_id):
    if 'logged_in' not in session or session['role'] != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    return Admin.deleteAmenity(amenity_id, None)

@app.route('/api/edit_amenity/<int:amenity_id>', methods=['GET', 'PUT'])
def edit_amenity(amenity_id):
    if 'logged_in' not in session or session['role'] != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    if request.method == 'PUT':
        data = request.get_json()
        return Admin.editAmenity(amenity_id, data['amenity_name'], data['amenity_description'], data.get('property_id'))
    try:
        res = supabase.table('amenities').select("*").eq("amenity_id", amenity_id).single().execute()
        return jsonify({"amenity": res.data})
    except Exception:
        return jsonify({"amenity": None})

@app.route('/api/view_rooms/<int:property_id>')
def view_rooms(property_id):
    if 'logged_in' not in session or session['role'] != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    rooms = Admin.viewRooms(property_id)
    return jsonify({"rooms": rooms, "property_id": property_id})

@app.route('/api/delete_room/<int:room_id>', methods=['DELETE'])
def delete_room(room_id):
    if 'logged_in' not in session or session['role'] != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    return Admin.deleteRoom(room_id, None)

@app.route('/api/add_room/<int:property_id>', methods=['POST'])
def add_room(property_id):
    if 'logged_in' not in session or session['role'] != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    data = request.get_json()
    return Admin.addRoom(
        property_id, data['room_type'], data['capacity'],
        data['price_per_night'], data.get('availability_status', True)
    )

@app.route('/api/edit_room/<int:room_id>', methods=['GET', 'PUT'])
def edit_room(room_id):
    if 'logged_in' not in session or session['role'] != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    if request.method == 'PUT':
        data = request.get_json()
        return Admin.editRoom(
            room_id, data['room_type'], data['capacity'],
            data['price_per_night'], data.get('availability_status', True),
            data.get('property_id')
        )
    try:
        res = supabase.table('rooms').select("*, PROPERTIES(property_id)").eq("room_id", room_id).single().execute()
        return jsonify({"room": res.data})
    except Exception:
        return jsonify({"status": "error", "message": "Room not found."}), 404

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5001))
    app.run(debug=True, port=port)
