#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════╗
║         RADIAX TECHNOLOGIES - AI CUSTOMER CARE SYSTEM             ║
║                    Advanced Voice AI Agent                        ║
║                                                                   ║
║  Features:                                                        ║
║  ✓ Real-time voice recognition (STT)                             ║
║  ✓ Natural text-to-speech (TTS)                                  ║
║  ✓ Phone call handling                                           ║
║  ✓ WhatsApp call integration                                     ║
║  ✓ Multi-language support                                        ║
║  ✓ Customer database                                             ║
║  ✓ Ticket system                                                 ║
║  ✓ Call logging & analytics                                      ║
║  ✓ Smart conversation flow                                       ║
╚═══════════════════════════════════════════════════════════════════╝
"""

import subprocess
import requests
import json
import time
import os
import re
import threading
import queue
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
import tempfile
import wave
import base64

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

CONFIG = {
    "company_name": "Radiax Technologies",
    "company_phone": "+254700000000",
    "working_hours": {"start": 8, "end": 22},
    "languages": ["en", "sw"],  # English, Swahili
    "default_language": "en",
    "max_call_duration": 600,  # 10 minutes
    "silence_timeout": 30,
    "recording_duration": 5,
    "sample_rate": 16000,
    "data_dir": os.path.expanduser("~/radiax-customer-care/data"),
    "audio_dir": os.path.expanduser("~/radiax-customer-care/audio"),
    "log_dir": os.path.expanduser("~/radiax-customer-care/logs"),
}

# Create directories
for dir_path in [CONFIG["data_dir"], CONFIG["audio_dir"], CONFIG["log_dir"]]:
    Path(dir_path).mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════
# AI APIs (Your Free APIs)
# ═══════════════════════════════════════════════════════════════════

AI_APIS = [
    {
        "name": "ZellAPI",
        "url": "https://zellapi.autos/ai/chatbot?text={}",
        "response_key": "result"
    },
    {
        "name": "Gemini",
        "url": "https://vapis.my.id/api/gemini?q={}",
        "response_key": "message"
    },
    {
        "name": "GeminiPro",
        "url": "https://api.siputzx.my.id/api/ai/gemini-pro?content={}",
        "response_key": "data"
    },
    {
        "name": "RyzenAI",
        "url": "https://api.ryzendesu.vip/api/ai/gemini?text={}",
        "response_key": "answer"
    },
    {
        "name": "GiftedAI",
        "url": "https://api.giftedtech.my.id/api/ai/geminiai?apikey=gifted&q={}",
        "response_key": "result"
    },
]

# ═══════════════════════════════════════════════════════════════════
# DATABASE MANAGER
# ═══════════════════════════════════════════════════════════════════

class Database:
    def __init__(self):
        self.db_path = os.path.join(CONFIG["data_dir"], "customers.db")
        self.init_db()
    
    def init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Customers table
        c.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                system_id TEXT UNIQUE,
                phone TEXT,
                name TEXT,
                email TEXT,
                language TEXT DEFAULT 'en',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_contact TIMESTAMP
            )
        ''')
        
        # Tickets table
        c.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT UNIQUE,
                customer_id INTEGER,
                subject TEXT,
                description TEXT,
                status TEXT DEFAULT 'open',
                priority TEXT DEFAULT 'normal',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP,
                resolved_at TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        ''')
        
        # Call logs table
        c.execute('''
            CREATE TABLE IF NOT EXISTS call_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                call_type TEXT,
                duration INTEGER,
                transcript TEXT,
                sentiment TEXT,
                started_at TIMESTAMP,
                ended_at TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        ''')
        
        # FAQ table
        c.execute('''
            CREATE TABLE IF NOT EXISTS faq (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT,
                answer TEXT,
                category TEXT,
                keywords TEXT
            )
        ''')
        
        # Insert default FAQs
        default_faqs = [
            ("What are your working hours?", "We are open from 8 AM to 10 PM, Monday to Sunday.", "general", "hours,open,time,working"),
            ("How do I reset my password?", "To reset your password, go to our website and click 'Forgot Password', then enter your email.", "account", "password,reset,forgot,login"),
            ("What payment methods do you accept?", "We accept M-Pesa, credit cards, and bank transfers.", "billing", "payment,pay,mpesa,card"),
            ("How can I track my order?", "You can track your order using your System ID on our website or by calling us.", "orders", "track,order,delivery,shipping"),
            ("How do I contact support?", "You can reach us via phone, WhatsApp, or email at support@radiax.co.ke", "support", "contact,support,help,reach"),
        ]
        
        for faq in default_faqs:
            try:
                c.execute("INSERT OR IGNORE INTO faq (question, answer, category, keywords) VALUES (?, ?, ?, ?)", faq)
            except:
                pass
        
        conn.commit()
        conn.close()
    
    def get_customer(self, system_id=None, phone=None):
        """Get customer by system_id or phone"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        if system_id:
            c.execute("SELECT * FROM customers WHERE system_id = ?", (system_id,))
        elif phone:
            c.execute("SELECT * FROM customers WHERE phone = ?", (phone,))
        else:
            return None
        
        row = c.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "system_id": row[1],
                "phone": row[2],
                "name": row[3],
                "email": row[4],
                "language": row[5],
                "created_at": row[6],
                "last_contact": row[7]
            }
        return None
    
    def create_customer(self, phone, name=None):
        """Create new customer"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Generate system ID
        system_id = "RAD" + hashlib.md5(phone.encode()).hexdigest()[:6].upper()
        
        try:
            c.execute(
                "INSERT INTO customers (system_id, phone, name) VALUES (?, ?, ?)",
                (system_id, phone, name)
            )
            conn.commit()
            customer_id = c.lastrowid
        except sqlite3.IntegrityError:
            # Customer exists
            c.execute("SELECT id, system_id FROM customers WHERE phone = ?", (phone,))
            row = c.fetchone()
            customer_id, system_id = row[0], row[1]
        
        conn.close()
        return system_id
    
    def update_customer(self, system_id, **kwargs):
        """Update customer info"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        updates = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [system_id]
        
        c.execute(f"UPDATE customers SET {updates}, last_contact = CURRENT_TIMESTAMP WHERE system_id = ?", values)
        conn.commit()
        conn.close()
    
    def create_ticket(self, customer_id, subject, description, priority="normal"):
        """Create support ticket"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        ticket_id = "TKT" + datetime.now().strftime("%Y%m%d%H%M%S")
        
        c.execute(
            "INSERT INTO tickets (ticket_id, customer_id, subject, description, priority) VALUES (?, ?, ?, ?, ?)",
            (ticket_id, customer_id, subject, description, priority)
        )
        conn.commit()
        conn.close()
        
        return ticket_id
    
    def get_tickets(self, customer_id, status=None):
        """Get customer tickets"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        if status:
            c.execute("SELECT * FROM tickets WHERE customer_id = ? AND status = ?", (customer_id, status))
        else:
            c.execute("SELECT * FROM tickets WHERE customer_id = ?", (customer_id,))
        
        rows = c.fetchall()
        conn.close()
        
        return [{"ticket_id": r[1], "subject": r[3], "status": r[5], "created_at": r[7]} for r in rows]
    
    def log_call(self, customer_id, call_type, duration, transcript, sentiment="neutral"):
        """Log call details"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute(
            "INSERT INTO call_logs (customer_id, call_type, duration, transcript, sentiment, started_at, ended_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (customer_id, call_type, duration, transcript, sentiment, datetime.now(), datetime.now())
        )
        conn.commit()
        conn.close()
    
    def search_faq(self, query):
        """Search FAQ by keywords"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        words = query.lower().split()
        results = []
        
        c.execute("SELECT question, answer, keywords FROM faq")
        rows = c.fetchall()
        
        for row in rows:
            score = sum(1 for word in words if word in row[2].lower())
            if score > 0:
                results.append({"question": row[0], "answer": row[1], "score": score})
        
        conn.close()
        return sorted(results, key=lambda x: x["score"], reverse=True)


# ═══════════════════════════════════════════════════════════════════
# VOICE ENGINE (TTS + STT)
# ═══════════════════════════════════════════════════════════════════

class VoiceEngine:
    def __init__(self):
        self.is_speaking = False
        self.is_listening = False
        self.audio_queue = queue.Queue()
    
    def speak(self, text, language="en"):
        """Text-to-Speech using Termux TTS"""
        self.is_speaking = True
        print(f"\n🔊 AI: {text}\n")
        
        try:
            # Try Termux TTS first
            lang_code = "en" if language == "en" else "sw-KE"
            result = subprocess.run(
                ["termux-tts-speak", "-l", lang_code, "-r", "1.0", text],
                timeout=120,
                capture_output=True
            )
            time.sleep(0.3)
            
        except subprocess.TimeoutExpired:
            print("(TTS timeout)")
        except FileNotFoundError:
            # Fallback: Use gTTS and play
            self._gtts_speak(text, language)
        except Exception as e:
            print(f"(TTS error: {e})")
        
        self.is_speaking = False
    
    def _gtts_speak(self, text, language):
        """Fallback TTS using Google TTS"""
        try:
            from gtts import gTTS
            
            audio_file = os.path.join(CONFIG["audio_dir"], "tts_output.mp3")
            tts = gTTS(text=text, lang=language)
            tts.save(audio_file)
            
            # Play using termux-media-player or sox
            subprocess.run(["play", audio_file], capture_output=True, timeout=60)
            os.remove(audio_file)
            
        except Exception as e:
            print(f"(gTTS error: {e})")
    
    def listen(self, duration=5, auto_detect=True):
        """Speech-to-Text using Termux microphone"""
        self.is_listening = True
        print("🎤 Listening...")
        
        audio_file = os.path.join(CONFIG["audio_dir"], "recording.wav")
        
        try:
            # Record using Termux
            subprocess.run([
                "termux-microphone-record",
                "-f", audio_file,
                "-l", str(duration),
                "-r", str(CONFIG["sample_rate"]),
                "-c", "1"
            ], timeout=duration + 5)
            
            time.sleep(duration + 1)
            
            # Stop recording
            subprocess.run(["termux-microphone-record", "-q"], timeout=5)
            
            # Transcribe
            text = self._transcribe(audio_file)
            
            # Cleanup
            if os.path.exists(audio_file):
                os.remove(audio_file)
            
            self.is_listening = False
            return text
            
        except Exception as e:
            print(f"(Listen error: {e})")
            self.is_listening = False
            
            # Fallback to manual input
            print("\n📝 [Manual input - what did caller say?]")
            return input(">>> ").strip()
    
    def _transcribe(self, audio_file):
        """Transcribe audio to text"""
        try:
            import speech_recognition as sr
            
            recognizer = sr.Recognizer()
            
            with sr.AudioFile(audio_file) as source:
                audio = recognizer.record(source)
            
            # Try Google Speech Recognition (free)
            text = recognizer.recognize_google(audio, language="en-US")
            print(f"📝 Heard: {text}")
            return text
            
        except Exception as e:
            print(f"(Transcription error: {e})")
            # Fallback to manual
            print("\n📝 [Manual input - what did caller say?]")
            return input(">>> ").strip()
    
    def listen_continuous(self, callback, stop_event):
        """Continuous listening with voice activity detection"""
        while not stop_event.is_set():
            if not self.is_speaking:
                text = self.listen(duration=5)
                if text:
                    callback(text)
            time.sleep(0.1)


# ═══════════════════════════════════════════════════════════════════
# AI BRAIN
# ═══════════════════════════════════════════════════════════════════

class AIBrain:
    def __init__(self, db):
        self.db = db
        self.context = []
        self.max_context = 10
        
        # System prompt
        self.system_prompt = f"""You are an AI customer care agent for {CONFIG['company_name']}.

GUIDELINES:
- Be helpful, professional, and friendly
- Keep responses SHORT (1-3 sentences max)
- If you don't know something, say so and offer to create a ticket
- For technical issues, gather details before creating a ticket
- Always confirm important actions before taking them

CAPABILITIES:
- Answer general questions
- Help with account issues
- Process support tickets
- Provide order/delivery status
- Handle complaints professionally

TONE: Professional but warm, like a helpful friend who works at the company."""

    def get_response(self, user_input, customer=None):
        """Get AI response"""
        
        # Add to context
        self.context.append({"role": "user", "content": user_input})
        if len(self.context) > self.max_context:
            self.context = self.context[-self.max_context:]
        
        # Check FAQ first
        faq_results = self.db.search_faq(user_input)
        if faq_results and faq_results[0]["score"] >= 2:
            response = faq_results[0]["answer"]
            self.context.append({"role": "assistant", "content": response})
            return response
        
        # Build query with context
        customer_info = ""
        if customer:
            customer_info = f"\nCustomer: {customer.get('name', 'Unknown')} (ID: {customer.get('system_id', 'N/A')})"
        
        context_text = "\n".join([f"{m['role']}: {m['content']}" for m in self.context[-5:]])
        
        query = f"""{self.system_prompt}
{customer_info}

Recent conversation:
{context_text}

Respond briefly to the customer's last message:"""
        
        # Try APIs
        response = self._call_ai_api(query)
        
        # Add to context
        self.context.append({"role": "assistant", "content": response})
        
        return response
    
    def _call_ai_api(self, query):
        """Call AI APIs with fallback"""
        
        for api in AI_APIS:
            try:
                url = api["url"].format(requests.utils.quote(query))
                resp = requests.get(url, timeout=20)
                data = resp.json()
                
                # Try different response keys
                answer = data.get(api["response_key"]) or data.get("result") or data.get("message") or data.get("data") or data.get("answer")
                
                if answer:
                    return self._clean_response(answer)
                    
            except Exception as e:
                continue
        
        return "I apologize, I'm having trouble processing that. Could you please repeat or rephrase?"
    
    def _clean_response(self, text):
        """Clean AI response for speech"""
        # Remove markdown
        text = re.sub(r'\[.*?\]\(.*?\)', '', text)
        text = re.sub(r'[*_#`]', '', text)
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'\n+', ' ', text)
        
        # Limit length
        if len(text) > 300:
            sentences = text.split('.')
            text = '.'.join(sentences[:3]) + '.'
        
        return text.strip()
    
    def analyze_intent(self, text):
        """Analyze user intent"""
        text_lower = text.lower()
        
        intents = {
            "greeting": ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"],
            "goodbye": ["bye", "goodbye", "see you", "thank you", "thanks", "that's all"],
            "problem": ["problem", "issue", "help", "support", "broken", "not working", "error"],
            "register": ["new", "register", "sign up", "first time", "create account"],
            "billing": ["bill", "payment", "pay", "invoice", "charge", "mpesa"],
            "order": ["order", "delivery", "track", "shipping", "package"],
            "complaint": ["complaint", "unhappy", "dissatisfied", "angry", "frustrated"],
            "human": ["human", "agent", "person", "operator", "real person", "speak to someone"],
            "hours": ["hours", "open", "close", "time", "available"],
            "contact": ["contact", "email", "phone", "reach", "address"],
        }
        
        for intent, keywords in intents.items():
            if any(kw in text_lower for kw in keywords):
                return intent
        
        return "general"
    
    def reset_context(self):
        """Reset conversation context"""
        self.context = []


# ═══════════════════════════════════════════════════════════════════
# CONVERSATION MANAGER
# ═══════════════════════════════════════════════════════════════════

class ConversationManager:
    def __init__(self):
        self.db = Database()
        self.voice = VoiceEngine()
        self.ai = AIBrain(self.db)
        
        self.state = "WELCOME"
        self.customer = None
        self.call_start = None
        self.transcript = []
        self.language = "en"
    
    def start_call(self, call_type="phone", caller_id=None):
        """Initialize a new call"""
        self.state = "WELCOME"
        self.customer = None
        self.call_start = datetime.now()
        self.transcript = []
        self.ai.reset_context()
        
        # Try to identify customer by phone
        if caller_id:
            self.customer = self.db.get_customer(phone=caller_id)
        
        print("\n" + "=" * 60)
        print(f"📞 NEW {call_type.upper()} CALL")
        print(f"⏰ Started: {self.call_start.strftime('%Y-%m-%d %H:%M:%S')}")
        if self.customer:
            print(f"👤 Customer: {self.customer.get('name', 'Unknown')} ({self.customer['system_id']})")
        print("=" * 60 + "\n")
    
    def end_call(self):
        """End the call and save logs"""
        duration = (datetime.now() - self.call_start).seconds if self.call_start else 0
        
        # Log call
        if self.customer:
            self.db.log_call(
                self.customer["id"],
                "phone",
                duration,
                json.dumps(self.transcript),
                "neutral"
            )
        
        print("\n" + "=" * 60)
        print("📞 CALL ENDED")
        print(f"⏱️ Duration: {duration // 60}m {duration % 60}s")
        print("=" * 60 + "\n")
        
        # Reset
        self.state = "WELCOME"
        self.customer = None
        self.call_start = None
        self.transcript = []
        self.ai.reset_context()
    
    def process(self, user_input):
        """Process user input and return response"""
        
        # Log transcript
        self.transcript.append({"role": "customer", "text": user_input, "time": datetime.now().isoformat()})
        
        # Analyze intent
        intent = self.ai.analyze_intent(user_input)
        
        # State machine
        response = self._handle_state(user_input, intent)
        
        # Log response
        self.transcript.append({"role": "agent", "text": response, "time": datetime.now().isoformat()})
        
        return response
    
    def _handle_state(self, user_input, intent):
        """Handle conversation states"""
        
        # ─────────────────────────────────────────────────────────
        # GOODBYE (can happen in any state)
        # ─────────────────────────────────────────────────────────
        if intent == "goodbye":
            self.state = "GOODBYE"
            if self.customer:
                return f"Thank you for calling {CONFIG['company_name']}, {self.customer.get('name', '')}! Have a wonderful day. Goodbye!"
            return f"Thank you for calling {CONFIG['company_name']}! Have a wonderful day. Goodbye!"
        
        # ─────────────────────────────────────────────────────────
        # TRANSFER TO HUMAN
        # ─────────────────────────────────────────────────────────
        if intent == "human":
            return "I understand you'd like to speak with a human agent. Let me transfer you. Please hold... Actually, I can help with most issues. What's your concern?"
        
        # ─────────────────────────────────────────────────────────
        # WELCOME STATE
        # ─────────────────────────────────────────────────────────
        if self.state == "WELCOME":
            if self.customer:
                # Returning customer
                self.state = "MAIN_MENU"
                return f"Welcome back to {CONFIG['company_name']}, {self.customer.get('name', '')}! How can I help you today?"
            
            if intent == "greeting":
                return f"Hello! Welcome to {CONFIG['company_name']}. Do you have an existing System ID, or are you a new customer?"
            
            if intent == "register" or "new" in user_input.lower():
                self.state = "REGISTER_PHONE"
                return "Welcome! I'll help you register. Please tell me your phone number."
            
            if intent == "problem" or any(w in user_input.lower() for w in ["existing", "yes", "have"]):
                self.state = "VERIFY_ID"
                return "Great! Please tell me your System ID for verification."
            
            # Default welcome
            return f"Welcome to {CONFIG['company_name']}! Are you an existing customer with a System ID, or would you like to register as a new customer?"
        
        # ─────────────────────────────────────────────────────────
        # VERIFY ID STATE
        # ─────────────────────────────────────────────────────────
        elif self.state == "VERIFY_ID":
            # Extract system ID
            system_id = self._extract_system_id(user_input)
            
            if system_id:
                customer = self.db.get_customer(system_id=system_id)
                
                if customer:
                    self.customer = customer
                    self.db.update_customer(system_id, last_contact=datetime.now())
                    self.state = "MAIN_MENU"
                    return f"Welcome back, {customer.get('name', 'valued customer')}! Your System ID {system_id} has been verified. How can I assist you today?"
                else:
                    return f"I couldn't find System ID {system_id} in our records. Please check and try again, or say 'register' to create a new account."
            else:
                return "I didn't catch your System ID. It usually starts with RAD followed by numbers. Please say it clearly."
        
        # ─────────────────────────────────────────────────────────
        # REGISTER PHONE STATE
        # ─────────────────────────────────────────────────────────
        elif self.state == "REGISTER_PHONE":
            phone = self._extract_phone(user_input)
            
            if phone:
                # Check if already exists
                existing = self.db.get_customer(phone=phone)
                if existing:
                    self.customer = existing
                    self.state = "MAIN_MENU"
                    return f"I found your account! Your System ID is {existing['system_id']}. How can I help you today?"
                
                self.temp_phone = phone
                self.state = "REGISTER_NAME"
                return f"Got it, {phone}. Now, what name should I register you under?"
            else:
                return "Please say your 10-digit phone number clearly, like: 0 7 1 2 3 4 5 6 7 8"
        
        # ─────────────────────────────────────────────────────────
        # REGISTER NAME STATE
        # ─────────────────────────────────────────────────────────
        elif self.state == "REGISTER_NAME":
            name = user_input.strip().title()
            
            if len(name) >= 2:
                # Create customer
                system_id = self.db.create_customer(self.temp_phone, name)
                self.customer = self.db.get_customer(system_id=system_id)
                self.state = "MAIN_MENU"
                
                return f"Perfect! Welcome to {CONFIG['company_name']}, {name}! Your System ID is {system_id}. Please save this for future reference. How can I help you today?"
            else:
                return "Please tell me your name."
        
        # ─────────────────────────────────────────────────────────
        # MAIN MENU STATE
        # ─────────────────────────────────────────────────────────
        elif self.state == "MAIN_MENU":
            if intent == "problem":
                self.state = "SUPPORT_DESCRIBE"
                return "I'm sorry to hear you're having an issue. Please describe your problem and I'll do my best to help."
            
            elif intent == "billing":
                return self._handle_billing(user_input)
            
            elif intent == "order":
                return self._handle_order(user_input)
            
            elif intent == "complaint":
                self.state = "COMPLAINT"
                return "I'm very sorry you're having a negative experience. Please tell me what happened, and I'll make sure this is addressed."
            
            elif intent == "hours":
                return f"We're open from {CONFIG['working_hours']['start']} AM to {CONFIG['working_hours']['end'] - 12} PM, Monday through Sunday. Is there anything else I can help with?"
            
            elif intent == "contact":
                return f"You can reach us at {CONFIG['company_phone']}, or email support@radiax.co.ke. Our office is in Nairobi. Anything else?"
            
            else:
                # Use AI for general queries
                return self.ai.get_response(user_input, self.customer)
        
        # ─────────────────────────────────────────────────────────
        # SUPPORT DESCRIBE STATE
        # ─────────────────────────────────────────────────────────
        elif self.state == "SUPPORT_DESCRIBE":
            self.temp_issue = user_input
            self.state = "SUPPORT_CONFIRM"
            return f"I understand. You're experiencing: {user_input[:100]}. Should I create a support ticket for this? Say yes to confirm."
        
        # ─────────────────────────────────────────────────────────
        # SUPPORT CONFIRM STATE
        # ─────────────────────────────────────────────────────────
        elif self.state == "SUPPORT_CONFIRM":
            if any(w in user_input.lower() for w in ["yes", "yeah", "sure", "ok", "confirm"]):
                # Create ticket
                if self.customer:
                    ticket_id = self.db.create_ticket(
                        self.customer["id"],
                        "Support Request",
                        self.temp_issue,
                        "normal"
                    )
                    self.state = "MAIN_MENU"
                    return f"Done! I've created ticket {ticket_id}. Our team will contact you within 24 hours. Is there anything else I can help with?"
                else:
                    self.state = "MAIN_MENU"
                    return "I'll need to verify your account first to create a ticket. What's your System ID?"
            else:
                self.state = "MAIN_MENU"
                return "No problem. Let me try to help directly. " + self.ai.get_response(self.temp_issue, self.customer)
        
        # ─────────────────────────────────────────────────────────
        # COMPLAINT STATE
        # ─────────────────────────────────────────────────────────
        elif self.state == "COMPLAINT":
            if self.customer:
                ticket_id = self.db.create_ticket(
                    self.customer["id"],
                    "Complaint",
                    user_input,
                    "high"
                )
                self.state = "MAIN_MENU"
                return f"I sincerely apologize for this experience. I've escalated your complaint with ticket {ticket_id}. A supervisor will contact you within 4 hours. Is there anything else?"
            else:
                self.state = "MAIN_MENU"
                return "I apologize for your experience. Please provide your System ID so I can properly log this complaint."
        
        # ─────────────────────────────────────────────────────────
        # DEFAULT - Use AI
        # ─────────────────────────────────────────────────────────
        return self.ai.get_response(user_input, self.customer)
    
    def _handle_billing(self, user_input):
        """Handle billing queries"""
        return "For billing inquiries, I can help with payment status, invoices, or M-Pesa payments. What specifically do you need help with?"
    
    def _handle_order(self, user_input):
        """Handle order queries"""
        return "For order tracking, please provide your order number or System ID, and I'll check the status for you."
    
    def _extract_system_id(self, text):
        """Extract System ID from text"""
        # Look for RAD followed by letters/numbers
        match = re.search(r'RAD[A-Z0-9]{5,8}', text.upper())
        if match:
            return match.group()
        
        # Look for just numbers that could be a system ID
        numbers = re.findall(r'\d+', text)
        if numbers:
            num_str = ''.join(numbers)
            if len(num_str) >= 5:
                return "RAD" + num_str[:6]
        
        return None
    
    def _extract_phone(self, text):
        """Extract phone number from text"""
        # Remove spaces and non-digits
        numbers = re.findall(r'\d+', text)
        phone = ''.join(numbers)
        
        # Kenyan format
        if len(phone) >= 9:
            if phone.startswith('254'):
                return '+' + phone
            elif phone.startswith('0'):
                return '+254' + phone[1:]
            elif phone.startswith('7') or phone.startswith('1'):
                return '+254' + phone
            else:
                return '+254' + phone[-9:]
        
        return None
    
    def get_welcome_message(self):
        """Get welcome message"""
        hour = datetime.now().hour
        
        if hour < 12:
            greeting = "Good morning"
        elif hour < 17:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        
        if self.customer:
            return f"{greeting}! Welcome back to {CONFIG['company_name']}, {self.customer.get('name', '')}! How can I assist you today?"
        
        return f"{greeting}! Thank you for calling {CONFIG['company_name']}. My name is Aria, your AI assistant. Do you have an existing System ID, or are you a new customer?"


# ═══════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════

class RadiaxCustomerCare:
    def __init__(self):
        self.conversation = ConversationManager()
        self.voice = self.conversation.voice
        self.running = False
        
        self._print_banner()
    
    def _print_banner(self):
        """Print startup banner"""
        banner = """
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║     ██████╗  █████╗ ██████╗ ██╗ █████╗ ██╗  ██╗                  ║
║     ██╔══██╗██╔══██╗██╔══██╗██║██╔══██╗╚██╗██╔╝                  ║
║     ██████╔╝███████║██║  ██║██║███████║ ╚███╔╝                   ║
║     ██╔══██╗██╔══██║██║  ██║██║██╔══██║ ██╔██╗                   ║
║     ██║  ██║██║  ██║██████╔╝██║██║  ██║██╔╝ ██╗                  ║
║     ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝                  ║
║                                                                   ║
║              🎧 AI CUSTOMER CARE SYSTEM 🎧                        ║
║                                                                   ║
║     • Real-time Voice Recognition                                 ║
║     • Natural Speech Synthesis                                    ║
║     • Intelligent Conversation AI                                 ║
║     • Customer Database                                           ║
║     • Ticket Management                                           ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
        """
        print(banner)
        print(f"✅ System initialized at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Data directory: {CONFIG['data_dir']}")
        print("")
    
    def run_phone_call(self):
        """Handle phone call"""
        print("\n" + "─" * 60)
        print("📞 PHONE CALL MODE")
        print("─" * 60)
        print("Instructions:")
        print("  1. Answer the incoming call on your phone")
        print("  2. Put it on speaker or connect audio")
        print("  3. Press ENTER to start the AI")
        print("─" * 60)
        
        input("\n>>> Press ENTER when call is connected...")
        
        self.conversation.start_call("phone")
        self.running = True
        
        # Welcome
        welcome = self.conversation.get_welcome_message()
        self.voice.speak(welcome)
        
        # Main loop
        while self.running:
            try:
                # Listen
                user_input = self.voice.listen(duration=CONFIG["recording_duration"])
                
                if not user_input:
                    self.voice.speak("I didn't catch that. Could you please repeat?")
                    continue
                
                # Process
                response = self.conversation.process(user_input)
                
                # Speak
                self.voice.speak(response)
                
                # Check if call should end
                if self.conversation.state == "GOODBYE":
                    break
                
            except KeyboardInterrupt:
                self.voice.speak(f"Thank you for calling {CONFIG['company_name']}. Goodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
                self.voice.speak("I'm sorry, there was an error. Let me try again.")
        
        self.conversation.end_call()
        self.running = False
    
    def run_whatsapp_mode(self):
        """Handle WhatsApp calls (voice notes simulation)"""
        print("\n" + "─" * 60)
        print("📱 WHATSAPP MODE")
        print("─" * 60)
        print("This mode simulates WhatsApp voice interaction.")
        print("In production, integrate with WhatsApp Business API.")
        print("─" * 60)
        
        self.conversation.start_call("whatsapp")
        self.running = True
        
        # Welcome
        welcome = self.conversation.get_welcome_message()
        self.voice.speak(welcome)
        
        # Same loop as phone
        while self.running:
            try:
                user_input = self.voice.listen(duration=CONFIG["recording_duration"])
                
                if not user_input:
                    self.voice.speak("I didn't catch that. Could you please repeat?")
                    continue
                
                response = self.conversation.process(user_input)
                self.voice.speak(response)
                
                if self.conversation.state == "GOODBYE":
                    break
                
            except KeyboardInterrupt:
                self.voice.speak("Thank you for contacting us. Goodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
        
        self.conversation.end_call()
        self.running = False
    
    def run_test_mode(self):
        """Test mode with text input"""
        print("\n" + "─" * 60)
        print("🧪 TEST MODE")
        print("─" * 60)
        print("Type messages to test the AI (no voice)")
        print("Type 'quit' to exit")
        print("─" * 60)
        
        self.conversation.start_call("test")
        
        # Welcome
        welcome = self.conversation.get_welcome_message()
        print(f"\n🤖 AI: {welcome}\n")
        
        while True:
            try:
                user_input = input("👤 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n🤖 AI: Thank you for testing. Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                response = self.conversation.process(user_input)
                print(f"\n🤖 AI: {response}\n")
                
                if self.conversation.state == "GOODBYE":
                    break
                
            except KeyboardInterrupt:
                print("\n\n👋 Test ended")
                break
        
        self.conversation.end_call()
    
    def show_menu(self):
        """Show main menu"""
        while True:
            print("\n" + "═" * 60)
            print("                    MAIN MENU")
            print("═" * 60)
            print("  1. 📞 Phone Call Mode")
            print("  2. 📱 WhatsApp Mode")
            print("  3. 🧪 Test Mode (Text)")
            print("  4. 📊 View Statistics")
            print("  5. ⚙️  Settings")
            print("  6. 🚪 Exit")
            print("═" * 60)
            
            choice = input("\nSelect option (1-6): ").strip()
            
            if choice == "1":
                self.run_phone_call()
            elif choice == "2":
                self.run_whatsapp_mode()
            elif choice == "3":
                self.run_test_mode()
            elif choice == "4":
                self.show_statistics()
            elif choice == "5":
                self.show_settings()
            elif choice == "6":
                print("\n👋 Goodbye!")
                break
            else:
                print("Invalid option. Please choose 1-6.")
    
    def show_statistics(self):
        """Show call statistics"""
        print("\n" + "─" * 60)
        print("📊 STATISTICS")
        print("─" * 60)
        
        db = self.conversation.db
        conn = sqlite3.connect(db.db_path)
        c = conn.cursor()
        
        # Total customers
        c.execute("SELECT COUNT(*) FROM customers")
        total_customers = c.fetchone()[0]
        
        # Total tickets
        c.execute("SELECT COUNT(*) FROM tickets")
        total_tickets = c.fetchone()[0]
        
        # Open tickets
        c.execute("SELECT COUNT(*) FROM tickets WHERE status = 'open'")
        open_tickets = c.fetchone()[0]
        
        # Total calls
        c.execute("SELECT COUNT(*) FROM call_logs")
        total_calls = c.fetchone()[0]
        
        conn.close()
        
        print(f"  👥 Total Customers: {total_customers}")
        print(f"  🎫 Total Tickets: {total_tickets}")
        print(f"  📬 Open Tickets: {open_tickets}")
        print(f"  📞 Total Calls: {total_calls}")
        print("─" * 60)
        
        input("\nPress ENTER to continue...")
    
    def show_settings(self):
        """Show settings"""
        print("\n" + "─" * 60)
        print("⚙️  SETTINGS")
        print("─" * 60)
        print(f"  Company: {CONFIG['company_name']}")
        print(f"  Phone: {CONFIG['company_phone']}")
        print(f"  Working Hours: {CONFIG['working_hours']['start']}:00 - {CONFIG['working_hours']['end']}:00")
        print(f"  Recording Duration: {CONFIG['recording_duration']}s")
        print(f"  Languages: {', '.join(CONFIG['languages'])}")
        print("─" * 60)
        
        input("\nPress ENTER to continue...")


# ═══════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        app = RadiaxCustomerCare()
        app.show_menu()
    except KeyboardInterrupt:
        print("\n\n👋 System shutdown")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
