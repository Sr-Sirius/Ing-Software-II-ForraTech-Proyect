# 🌱 ForraTech AI — Intelligent Forage Recommendation System

> Bridging traditional livestock farming with Artificial Intelligence for sustainable sheep and goat production in Colombia.

---

# 📌 Overview

**ForraTech AI** is an intelligent forage recommendation platform designed for small and medium-sized sheep and goat producers in **Guachetá, Cundinamarca (Colombia)**.

The project integrates:

* 🌾 Precision Agriculture
* 🤖 Machine Learning
* 📊 Agricultural Data Analysis
* 🌐 Flask Web Technologies
* ☁️ Cloud Deployment

to generate real-time forage recommendations based on environmental and productive variables.

---

# 🎯 Project Objective

The goal of ForraTech AI is to help livestock producers optimize forage selection through data-driven recommendations instead of empirical trial-and-error practices.

The system analyzes variables such as:

* Soil pH
* Humidity
* Temperature
* Altitude
* Climate conditions
* Protein target

to recommend optimal forage species for sheep and goat production.

---

# 🧠 Machine Learning Models

The platform includes experimentation and implementation of multiple Machine Learning algorithms:

| Model               | Type         | Purpose                         |
| ------------------- | ------------ | ------------------------------- |
| Logistic Regression | Supervised   | Binary classification           |
| Naive Bayes         | Supervised   | Probabilistic inference         |
| KNN                 | Supervised   | Similarity-based recommendation |
| Random Forest       | Supervised   | Final selected production model |
| K-Means             | Unsupervised | Cluster analysis and grouping   |

---

# 🏆 Final Selected Model

## Random Forest Classifier

The best-performing model was **Random Forest**, achieving:

| Metric    | Result |
| --------- | ------ |
| Accuracy  | 99.5%  |
| Precision | 100%   |
| Recall    | 98.4%  |
| ROC AUC   | 0.998  |

### Why Random Forest?

* Handles non-linear relationships effectively
* High stability against overfitting
* Excellent generalization
* Robust performance with agricultural variables

---

# 🏗️ Project Architecture

The project follows a modular architecture using Flask and Machine Learning pipelines.

## Main Components

```text
Frontend (HTML/CSS/JS)
        ↓
Flask Backend Services
        ↓
Machine Learning Pipelines
        ↓
Serialized Models (.joblib)
        ↓
Real-Time Recommendation System
```

---

# 🔄 Methodology — CRISP-ML

The development process follows the **CRISP-ML** methodology:

1. Business Understanding
2. Data Understanding
3. Data Engineering
4. Modeling
5. Evaluation
6. Deployment

This ensured alignment between technical development and real agricultural needs.

---

# 📊 Datasets

The system was trained using two main sources:

## 1. Synthetic Dataset

* 1,000 generated records
* Used for rapid prototyping and testing

## 2. ENA-DANE Dataset

* Real Colombian agricultural data
* Used for environmental validation and realism

---

# ⚙️ Data Engineering

Implemented preprocessing pipeline:

* Missing value handling
* Outlier detection
* StandardScaler normalization
* Categorical encoding
* Feature engineering
* Composite environmental scores

---

# 🌐 Web Application Features

## Intelligent Recommendation Systems

* Random Forest recommendations
* Logistic Regression analysis
* Bayesian recommendation system
* K-Means clustering visualization

## Interactive Dashboards

* Real-time predictions
* Recommendation rankings
* Variable importance analysis
* ROC curves and confusion matrices

## Encyclopedia Module

Interactive encyclopedia for:

* 🐑 Sheep
* 🐐 Goats
* 🌿 Forage species

Including:

* Breed information
* Production types
* Nutritional characteristics
* Agricultural resources

---

# 🎨 Design Philosophy

## “The Digital Field”

ForraTech AI combines:

* Colombian rural landscapes
* Modern AI visualization
* High-tech agricultural aesthetics

### Color Palette

| Color         | Hex     |
| ------------- | ------- |
| Emerald Green | #2D6A4F |
| Mint White    | #F8F9FA |
| Charcoal Gray | #212529 |

---

# ☁️ Deployment

The platform is publicly deployed using **Render.com**.

## Live Demo

🔗 https://ing-software-ii-forratech-proyect.onrender.com

---

# 🛠️ Technologies Used

## Backend

* Flask
* Python
* Scikit-learn
* Pandas
* NumPy
* Joblib

## Frontend

* HTML5
* CSS3
* JavaScript

## Visualization

* Matplotlib
* Seaborn
* Plotly

## Deployment

* Render.com
* GitHub

---

# 📂 Project Structure

```text
ForraTech-AI/
│
├── app/
│   ├── routes/
│   ├── templates/
│   ├── static/
│   ├── models/
│   └── services/
│
├── datasets/
│
├── notebooks/
│
├── trained_models/
│
├── documentation/
│
├── requirements.txt
│
├── app.py
│
└── README.md
```

---

# 🚀 Installation

## Clone Repository

```bash
git clone https://github.com/your-repository/forratech-ai.git
```

## Enter Project

```bash
cd forratech-ai
```

## Create Virtual Environment

```bash
python -m venv venv
```

## Activate Environment

### Windows

```bash
venv\Scripts\activate
```

### Linux / Mac

```bash
source venv/bin/activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Run Application

```bash
python app.py
```

---

# 📈 Future Improvements

* Integration with IoT sensors
* Satellite climate monitoring
* Mobile application
* Automated forage prediction APIs
* Larger agricultural datasets
* Multi-region support

---

# 🌎 Sustainable Development Goals

ForraTech AI supports:

## SDG 12 — Responsible Production and Consumption

By promoting:

* Efficient resource usage
* Sustainable livestock planning
* Data-driven agricultural decisions

---

# 👥 Authors

## Michael

Systems Engineering Student

## David

Systems Engineering Student

Universidad de Cundinamarca

---

# 🙏 Acknowledgements

Special thanks to:

* ASOFINA producers association
* Universidad de Cundinamarca
* Machine Learning course professors
* Software Engineering II course
* Secure Software Development course

for their guidance and support during the development of this project.

---

# 📚 References

* DANE — National Agricultural Survey (ENA)
* FAO — FAOSTAT Database
* AGROSAVIA
* Scikit-learn Documentation
* Flask Documentation

---

# 📜 License

This project was developed for academic and research purposes.

---
