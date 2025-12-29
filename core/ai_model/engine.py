import pandas as pd
import os
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, 'dataset.csv')

class CivicAI:
    def __init__(self):
        self.model = None
        
        # KEYWORDS (Safety First - Ye kabhi fail nahi honge)
        self.priority_keywords = {
            'High': ['fire', 'blast', 'spark', 'current', 'death', 'accident', 'blood', 'murder', 'robbery', 'gas leak', 'live wire', 'poison', 'emergency', 'collapse', 'drowning', 'snatching', 'attack'],
            'Medium': ['garbage', 'smell', 'leak', 'jam', 'broken', 'dirty', 'mosquito', 'dengue', 'stagnant', 'theft', 'traffic', 'sewage', 'choked'],
            'Low': ['park', 'bench', 'grass', 'paint', 'faded', 'poster', 'banner', 'cleaning', 'leaves', 'parking']
        }

        # DEPARTMENT KEYWORDS
        self.dept_keywords = {
            'Electricity': ['light', 'pole', 'wire', 'current', 'power', 'meter', 'voltage', 'transformer'],
            'Water': ['water', 'pipe', 'tap', 'leakage', 'supply', 'tank', 'drain'],
            'Police': ['theft', 'robbery', 'fight', 'crime', 'traffic', 'signal', 'noise', 'stolen'],
            'PWD': ['road', 'pothole', 'bridge', 'street', 'divider', 'repair'],
            'Health': ['mosquito', 'dengue', 'malaria', 'food', 'hospital', 'dog', 'medicine'],
            'Fire': ['fire', 'smoke', 'blast', 'cylinder', 'gas'],
            'Municipal': ['garbage', 'dustbin', 'cleaning', 'tree', 'park', 'encroachment', 'toilet']
        }

        # ML Training (Department Detection)
        try:
            if os.path.exists(CSV_PATH):
                # 3 Column wala CSV padhna
                self.data = pd.read_csv(CSV_PATH, names=['text', 'label', 'priority'], header=0)
                
                # Department Model Train karo
                self.model = make_pipeline(TfidfVectorizer(), MultinomialNB())
                self.model.fit(self.data['text'], self.data['label'])
                print("✅ AI Engine Trained with Priority Data")
            else:
                print("⚠️ Dataset not found.")
        except Exception as e:
            print(f"⚠️ Training Error: {e}")

    def predict(self, text):
        text_lower = text.lower()
        predicted_dept = "Municipal" # Default
        predicted_prio = "Low"     # Default

        # 1. PRIORITY DETECTION (Keyword is safest)
        for word in self.priority_keywords['High']:
            if re.search(r'\b' + re.escape(word) + r'\b', text_lower):
                predicted_prio = "High"
                break
        if predicted_prio == "Low":
            for word in self.priority_keywords['Medium']:
                if re.search(r'\b' + re.escape(word) + r'\b', text_lower):
                    predicted_prio = "Medium"
                    break
        
        # 2. DEPARTMENT DETECTION (ML + Fallback)
        if self.model:
            try:
                predicted_dept = self.model.predict([text])[0]
            except: pass
        
        # Fallback Check
        found_keyword = False
        for dept, keywords in self.dept_keywords.items():
            for word in keywords:
                if re.search(r'\b' + re.escape(word) + r'\b', text_lower):
                    if not found_keyword: 
                        predicted_dept = dept
                        found_keyword = True
        
        return predicted_dept, predicted_prio

ai_bot = CivicAI()