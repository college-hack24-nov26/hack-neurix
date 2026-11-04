"""
HomeCare+ — Symptom-to-Disease ML Model Trainer
Trains a Random Forest classifier using a synthetic medical dataset.
Run: python backend/ml/train_model.py

Output: backend/ml/models/symptom_model.pkl
"""
import pickle
import numpy as np
import os
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score

# ── Training dataset ───────────────────────────────────────────────────────────
# Each entry: (symptom_text, disease_label)
# In production, replace with a real clinical dataset (e.g., MIMIC, PrimaDiagnosis)
TRAINING_DATA = [
    # Common Cold
    ("runny nose sneezing sore throat cough mild fever fatigue", "Common Cold"),
    ("nasal congestion runny nose mild headache cough sneezing", "Common Cold"),
    ("sore throat runny nose sneezing congestion", "Common Cold"),
    ("mild fever cough runny nose nasal congestion headache", "Common Cold"),
    ("sneezing watery eyes runny nose scratchy throat", "Common Cold"),

    # Influenza
    ("high fever body aches severe fatigue headache chills cough", "Influenza (Flu)"),
    ("fever muscle pain fatigue weakness chills sweating", "Influenza (Flu)"),
    ("sudden high fever severe headache body aches loss appetite", "Influenza (Flu)"),
    ("fever chills sweating fatigue cough sore throat", "Influenza (Flu)"),
    ("high fever body aches headache fatigue weakness cough", "Influenza (Flu)"),

    # Hypertension
    ("headache dizziness blurred vision chest pain shortness breath", "Hypertension"),
    ("severe headache nosebleed dizziness palpitations", "Hypertension"),
    ("headache neck pain vision problems fatigue", "Hypertension"),
    ("headache dizziness fatigue shortness breath", "Hypertension"),
    ("nosebleed severe headache blurred vision", "Hypertension"),

    # Diabetes
    ("frequent urination excessive thirst unexplained weight loss fatigue", "Type 2 Diabetes"),
    ("blurred vision frequent urination increased hunger fatigue", "Type 2 Diabetes"),
    ("slow healing wounds numbness tingling frequent urination excessive thirst", "Type 2 Diabetes"),
    ("fatigue blurred vision frequent urination weight loss", "Type 2 Diabetes"),
    ("excessive thirst frequent urination fatigue weakness numbness", "Type 2 Diabetes"),

    # Asthma
    ("wheezing shortness breath chest tightness coughing night", "Asthma"),
    ("difficulty breathing wheezing chest tightness", "Asthma"),
    ("shortness breath wheezing cough chest tightness exercise", "Asthma"),
    ("coughing night wheezing shortness breath", "Asthma"),
    ("chest tightness wheezing breathlessness", "Asthma"),

    # Migraine
    ("severe throbbing headache nausea vomiting sensitivity light sound", "Migraine"),
    ("pulsing headache one side nausea sensitivity light", "Migraine"),
    ("severe headache visual aura nausea vomiting", "Migraine"),
    ("headache nausea vomiting light sensitivity noise sensitivity", "Migraine"),
    ("throbbing one sided headache visual disturbances nausea", "Migraine"),

    # GERD
    ("heartburn regurgitation chest pain difficulty swallowing sour taste", "GERD"),
    ("burning chest heartburn acid taste throat", "GERD"),
    ("heartburn regurgitation bloating difficulty swallowing", "GERD"),
    ("chest burning after eating acid reflux sour taste", "GERD"),
    ("heartburn burning sensation chest regurgitation", "GERD"),

    # UTI
    ("burning urination frequent urination cloudy urine pelvic pain", "Urinary Tract Infection"),
    ("pain urination frequent urge urinate blood urine", "Urinary Tract Infection"),
    ("burning urination fever pelvic pain strong odor urine", "Urinary Tract Infection"),
    ("urinary frequency urgency burning painful urination", "Urinary Tract Infection"),
    ("cloudy urine strong smell frequent urination pain", "Urinary Tract Infection"),

    # Anemia
    ("fatigue weakness pale skin shortness breath dizziness cold", "Anemia"),
    ("tiredness weakness pale skin cold hands feet headache", "Anemia"),
    ("fatigue dizziness shortness breath pale gums", "Anemia"),
    ("weakness fatigue cold sensitivity brittle nails pale skin", "Anemia"),
    ("fatigue headache dizziness pale skin weakness", "Anemia"),

    # Allergic Rhinitis
    ("sneezing runny nose nasal congestion itchy eyes watery eyes", "Allergic Rhinitis"),
    ("itchy nose sneezing watery eyes nasal congestion", "Allergic Rhinitis"),
    ("runny nose sneezing itchy throat itchy eyes seasonal", "Allergic Rhinitis"),
    ("sneezing watery runny nose itchy eyes throat", "Allergic Rhinitis"),
    ("nasal congestion sneezing watery eyes itchy", "Allergic Rhinitis"),

    # Pneumonia
    ("cough phlegm fever chills shortness breath chest pain sweating", "Pneumonia"),
    ("productive cough fever difficulty breathing chest pain", "Pneumonia"),
    ("high fever cough green phlegm chest pain breathlessness", "Pneumonia"),
    ("fever chills cough breathlessness chest pain fatigue", "Pneumonia"),
    ("high temperature cough phlegm shortness breath", "Pneumonia"),

    # Appendicitis
    ("right lower abdominal pain nausea vomiting fever loss appetite", "Appendicitis"),
    ("severe abdominal pain right side fever nausea", "Appendicitis"),
    ("abdominal pain right lower quadrant vomiting fever", "Appendicitis"),
    ("right side stomach pain nausea fever loss appetite", "Appendicitis"),
    ("severe right abdominal pain fever nausea tenderness", "Appendicitis"),

    # Dengue
    ("high fever severe headache eye pain joint pain muscle pain rash", "Dengue Fever"),
    ("sudden high fever headache retro orbital pain joint muscle ache", "Dengue Fever"),
    ("fever rash joint pain muscle ache bleeding gums", "Dengue Fever"),
    ("high fever headache skin rash joint pain fatigue", "Dengue Fever"),
    ("fever body pain skin rash low platelet", "Dengue Fever"),

    # Malaria
    ("cyclical fever chills sweating headache nausea fatigue", "Malaria"),
    ("fever every two days chills shaking muscle ache", "Malaria"),
    ("periodic fever chills sweating vomiting fatigue", "Malaria"),
    ("recurring fever chills headache muscle pain", "Malaria"),
    ("fever chills sweating cycle headache nausea", "Malaria"),

    # Hypothyroidism
    ("fatigue weight gain cold sensitivity dry skin constipation depression", "Hypothyroidism"),
    ("tiredness weight gain cold intolerance hair loss", "Hypothyroidism"),
    ("fatigue cold hands feet weight gain dry skin", "Hypothyroidism"),
    ("slow heart rate constipation depression weight gain", "Hypothyroidism"),
    ("fatigue weight gain difficulty concentrating hair thinning", "Hypothyroidism"),

    # Rheumatoid Arthritis
    ("joint pain joint swelling stiffness morning fatigue", "Rheumatoid Arthritis"),
    ("multiple joint pain swelling warmth morning stiffness", "Rheumatoid Arthritis"),
    ("symmetric joint pain stiffness fatigue fever", "Rheumatoid Arthritis"),
    ("joint inflammation pain stiffness fatigue", "Rheumatoid Arthritis"),
    ("joint aching swelling stiffness morning", "Rheumatoid Arthritis"),

    # Depression
    ("persistent sadness loss interest fatigue sleep problems hopelessness", "Depression"),
    ("low mood worthlessness insomnia appetite change", "Depression"),
    ("sadness crying fatigue concentration problems", "Depression"),
    ("depression anxiety sleep disturbance loss enjoyment", "Depression"),
    ("low energy mood sadness social withdrawal", "Depression"),

    # Gastroenteritis
    ("nausea vomiting diarrhea abdominal cramps fever dehydration", "Gastroenteritis"),
    ("stomach pain vomiting loose stools fever", "Gastroenteritis"),
    ("diarrhea nausea vomiting abdominal pain fever", "Gastroenteritis"),
    ("loose motions vomiting stomach cramps fever", "Gastroenteritis"),
    ("vomiting diarrhea abdominal cramping loss appetite", "Gastroenteritis"),

    # Kidney Stones
    ("severe flank pain blood urine painful urination nausea", "Kidney Stones"),
    ("extreme back pain urinary frequency vomiting", "Kidney Stones"),
    ("severe side back pain urination blood nausea", "Kidney Stones"),
    ("sharp flank pain cloudy urine nausea vomiting", "Kidney Stones"),
    ("excruciating pain side abdomen blood urine", "Kidney Stones"),
]


def train_model():
    print("Training HomeCare+ Symptom-Disease ML Model...")

    # Prepare data
    texts  = [item[0] for item in TRAINING_DATA]
    labels = [item[1] for item in TRAINING_DATA]

    # Encode labels
    le = LabelEncoder()
    y  = le.fit_transform(labels)

    # TF-IDF vectoriser
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=1,
        max_features=5000,
        analyzer="word",
    )
    X = vectorizer.fit_transform(texts)

    # Train / test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # Train Random Forest
    clf = RandomForestClassifier(
        n_estimators     = 200,
        max_depth        = None,
        min_samples_leaf = 1,
        random_state     = 42,
        class_weight     = "balanced",
        n_jobs           = -1,
    )
    clf.fit(X_train, y_train)

    # Evaluate
    y_pred = clf.predict(X_test)
    acc    = accuracy_score(y_test, y_pred)
    print(f"\nAccuracy on test set: {acc:.2%}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    # Cross-validation
    cv_scores = cross_val_score(clf, X, y, cv=5, scoring="accuracy")
    print(f"\nCross-validation accuracy: {cv_scores.mean():.2%} ± {cv_scores.std():.2%}")

    # Save model bundle
    out_dir = Path(__file__).parent / "models"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "symptom_model.pkl"

    bundle = {
        "model":         clf,
        "vectorizer":    vectorizer,
        "label_encoder": le,
        "diseases":      list(le.classes_),
        "training_size": len(TRAINING_DATA),
        "accuracy":      round(acc, 4),
    }
    with open(out_path, "wb") as f:
        pickle.dump(bundle, f)

    print(f"\nModel saved to: {out_path}")
    print(f"Diseases covered: {len(le.classes_)}")
    return out_path


if __name__ == "__main__":
    train_model()
