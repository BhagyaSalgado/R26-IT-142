# 🎬 AI-Powered Movie Trailer Analyzer for Predicting Audience Reactions and Engagement

Welcome to the **AI-Powered Movie Trailer Analyzer**, a research-based intelligent analytics platform designed to predict audience reactions and engagement toward movie trailers. The system combines **video analysis**, **audio feature extraction**, **viewer comment sentiment analysis**, **popularity metric analysis**, and an **explainable recommendation engine** to support film studios, content creators, streaming platforms, and digital marketing teams.

This project is developed under the research title:

**AI-Powered Movie Trailer Analyzer for Predicting Audience Reactions and Engagement**  
**Research Code:** R26-IT-142  
**Institution:** Sri Lanka Institute of Information Technology  
**Research Area:** Artificial Intelligence, Data Science, Multimedia Analytics, and Predictive Analytics

---

## 🧭 Table of Contents

1. [Project Overview](#-project-overview)
2. [Research Problem](#-research-problem)
3. [Research Gap](#-research-gap)
4. [Objectives](#-objectives)
5. [System Components](#-system-components)
6. [Technologies Used](#️-technologies-used)
7. [System Architecture](#-system-architecture)
8. [Data Flow](#-data-flow)
9. [Team Members](#-team-members)


---

## 📋 Project Overview

Movie trailers are one of the most powerful marketing tools used by the film industry to attract audience attention before a movie is officially released. With the growth of platforms such as **YouTube**, audiences now react to trailers through views, likes, comments, shares, and engagement behaviour.

However, predicting how audiences will respond to a trailer is still a difficult task. Many existing methods depend on manual observation, focus groups, post-release feedback, or basic engagement statistics. These approaches are often slow, expensive, subjective, and unable to provide deep insights before marketing decisions are made.

The **AI-Powered Movie Trailer Analyzer** solves this problem by using artificial intelligence to analyse multiple trailer-related signals:

- Visual content from trailer scenes
- Audio and music features
- Viewer comments and sentiment
- Popularity metrics such as views, likes, and comments
- Multimodal feature fusion for final prediction
- Explainable recommendation cards for trailer improvement

The system aims to help film studios, digital marketers, streaming platforms, and independent creators make better data-driven decisions about trailer performance and audience engagement.

---

## ❗ Research Problem

Film production companies and marketing teams often struggle to understand how audiences will react to movie trailers before or during public release. Although online platforms provide large amounts of engagement data, these data sources are usually fragmented and difficult to interpret manually.

Current approaches have several limitations:

- Manual analysis of audience reactions is time-consuming.
- Basic metrics such as views and likes do not explain why audiences react positively or negatively.
- Comment analysis is difficult due to slang, emojis, sarcasm, and informal language.
- Video, audio, sentiment, and popularity data are often analysed separately.
- Many systems stop at prediction and do not provide clear improvement recommendations.

Therefore, there is a need for an AI-powered system that can combine multiple trailer-related signals and generate accurate, explainable, and actionable insights.

---

## 🔬 Research Gap

Existing movie analytics and sentiment analysis systems mainly focus on one area such as box-office prediction, social media sentiment, movie reviews, or general engagement metrics. However, there is limited research on a complete trailer-specific system that combines multiple analytical dimensions.

The major research gaps addressed by this project are:

| Existing Limitation | Proposed Solution |
|---|---|
| Trailer analysis often depends on manual interpretation | Automated AI-based analysis pipeline |
| Systems mainly analyse only text, only popularity, or only video/audio | Multimodal analysis using video, audio, comments, and metrics |
| Basic sentiment tools struggle with informal trailer comments | NLP and transformer-based comment sentiment analysis |
| Popularity metrics are often used only descriptively | Machine learning-based popularity prediction |
| Video/audio analysis rarely provides scene-level emotional intensity | Per-scene emotional intensity scoring |
| Prediction systems often lack actionable recommendations | Explainable recommendation engine using MTIRF |

The novelty of this project is the integration of four AI-based components into a unified system for predicting audience reactions and generating improvement recommendations for movie trailers.

---

## 🎯 Objectives

### Main Objective

To design and develop an AI-powered movie trailer analysis system that predicts audience reactions and engagement by combining video/audio features, viewer comment sentiment, popularity metrics, and an explainable recommendation framework.

### Specific Objectives

- To analyse movie trailer scenes using video and audio processing techniques.
- To extract object, emotion, scene type, motion, and acoustic features from trailers.
- To collect and analyse viewer comments using Natural Language Processing.
- To classify audience comments into positive, negative, and neutral sentiment categories.
- To collect trailer popularity metrics such as views, likes, comments, and engagement ratios.
- To predict audience reaction levels using machine learning models.
- To combine outputs from all analytical components into a unified trailer profile.
- To generate ranked recommendation cards for improving trailer effectiveness.
- To present prediction results and insights through a user-friendly dashboard.

---

## 🧩 System Components

The overall system is divided into four main research components.

---

### 1. 🎥 Video and Audio Analysis Component

This component focuses on processing movie trailer visuals and audio signals to extract meaningful cinematic and emotional features. It also integrates the frontend dashboard interface that allows users to search, explore, and analyze movie trailers through an interactive user experience.

#### Key Functions

- Process trailer video frames and audio streams.
- Extract scene-level visual and emotional features.
- Perform motion and object detection.
- Analyze soundtrack and acoustic intensity.
- Provide a responsive frontend dashboard for trailer analysis.
- Display analytical outputs and recommendation insights.

#### Main Features

- Scene analysis
- Motion intensity detection
- Audio energy analysis
- Emotional intensity scoring
- Trailer exploration dashboard
- Responsive UI components
- Search and navigation interface
- Interactive analytical views

#### Main Technologies

- Python
- OpenCV
- YOLOv8
- DeepFace
- Librosa
- FFmpeg
- React.js
- JavaScript / TypeScript
- Tailwind CSS / Bootstrap
- Vite / CRA

#### Machine Learning Algorithms

- Object Detection Models
- Emotion Recognition Models
- Audio Feature Extraction
- Scene Classification Models

#### Output

The component produces scene-level trailer insights, audio-visual analytical outputs, and an interactive frontend dashboard for trailer exploration and prediction visualization.

---

### 2. 📊 Popularity Metrics Analysis Component

This component focuses on analysing trailer engagement metrics from online platforms. It uses machine learning to identify patterns between popularity metrics and audience reactions.

#### Key Functions

- Collect trailer engagement metrics from YouTube.
- Analyse views, likes, comments, and engagement ratios.
- Create structured datasets for machine learning.
- Perform feature engineering using popularity indicators.
- Predict audience reaction levels based on engagement metrics.
- Generate visual insights through charts and dashboards.

#### Main Features

- View count
- Like count
- Comment count
- Like ratio
- Engagement rate
- Popularity score
- View growth indicators

#### Main Technologies

- Python
- YouTube Data API
- Pandas
- NumPy
- Scikit-learn
- Matplotlib
- Seaborn

#### Machine Learning Algorithms

- Logistic Regression
- Random Forest
- Support Vector Machine

#### Output

The component produces popularity-based prediction results and engagement trend visualizations.

---

### 3. 💬 Viewer Comment Sentiment Analysis Component

This component ingests YouTube comments for movie trailers, preprocesses text, detects language, extracts topics, and classifies sentiment using a BERT-based model. It provides audience opinion insights and sentiment distributions through a REST API.

#### Key Functions

- Collect viewer comments using the YouTube Data API.
- Clean and normalize comment text.
- Detect language for multilingual support.
- Perform topic extraction and keyword clustering.
- Classify comments into positive, neutral, and negative sentiment categories.
- Provide sentiment analytics through JSON API responses.

#### Main Features

- Sentiment classification
- Language detection
- Topic extraction
- Comment preprocessing pipeline
- Sentiment distribution analytics
- Confidence scoring
- API integration support

#### Main Technologies

- Python 3.9+
- PyTorch / TensorFlow
- Hugging Face Transformers
- NLTK / spaCy
- Flask / FastAPI
- MongoDB

#### Machine Learning Algorithms

- BERT-based Sentiment Classification
- Transformer Models
- Frequency-based Topic Extraction
- Keyword Clustering

#### Output

The component produces sentiment distributions, topic analysis, confidence scores, and audience opinion insights for movie trailers.

---

### 4. 🧠 Content Insight and Recommendation Engine

This component analyses multimodal trailer data and generates creator-facing insights and ranked improvement recommendations. It predicts audience reaction levels and identifies weak content areas using explainable AI techniques.

#### Key Functions

- Predict audience reaction levels.
- Analyse trailer performance features.
- Compare trailer metrics with benchmark values.
- Generate ranked improvement recommendations.
- Identify high-impact trailer improvement areas.
- Support dashboard insight generation.

#### Main Features

- Audience reaction prediction
- Recommendation priority scoring
- Feature importance analysis
- Benchmark gap analysis
- Engagement forecasting
- Sentiment split analysis
- Scene intensity insights
- Recommendation cards

#### Main Technologies

- Python
- FastAPI
- Random Forest
- Scikit-learn
- Pandas
- Joblib
- React.js
- Recharts

#### Machine Learning Algorithms

- Random Forest
- Feature Importance Analysis
- Benchmark-based Recommendation Logic

#### Output

The component produces predicted audience reactions, audience scores, feature contribution values, dashboard insights, and ranked recommendation cards for trailer improvement.

---

## 🛠️ Technologies Used

| Technology / Tool | Purpose |
|---|---|
| **Python** | Main programming language for AI and analytics development |
| **YouTube Data API** | Collect trailer metadata, comments, and engagement metrics |
| **OpenCV** | Frame extraction, video processing, and motion analysis |
| **YOLOv8** | Object detection in trailer frames |
| **DeepFace** | Facial emotion recognition |
| **CLIP** | Zero-shot scene type classification |
| **Librosa** | Audio feature extraction |
| **FFmpeg** | Audio and video processing |
| **yt-dlp** | Trailer video downloading for analysis |
| **Pandas / NumPy** | Data processing, cleaning, and feature engineering |
| **Scikit-learn** | Machine learning model development and evaluation |
| **BERT** | Transformer-based sentiment classification |
| **TensorFlow / PyTorch** | Deep learning model implementation |
| **NLTK / spaCy** | Natural Language Processing preprocessing |
| **MongoDB Atlas** | Storage of trailer features, predictions, and recommendations |
| **FastAPI** | Backend API development |
| **Matplotlib / Seaborn** | Data visualization and analytical charts |
| **Web Dashboard** | Displaying predictions, insights, and recommendation cards |

---

## 🏗️ System Architecture

The system follows a modular architecture where each component processes a specific type of trailer-related data and sends structured outputs to the final prediction and recommendation layer.


### Main Layers

1. **Data Acquisition Layer**
   - Collects trailer videos, audio, comments, and engagement metrics from YouTube.

2. **Processing Layer**
   - Preprocesses video, audio, text, and popularity data.

3. **AI Analysis Layer**
   - Applies computer vision, NLP, audio analysis, and machine learning models.

4. **Feature Fusion Layer**
   - Combines outputs from all components into a unified trailer profile.

5. **Prediction and Recommendation Layer**
   - Predicts audience reaction and generates improvement recommendations.

6. **Dashboard Layer**
   - Displays results, charts, prediction labels, and recommendation cards.

---

## 🔄 Data Flow

```text
Movie Trailer / YouTube URL
        ↓
Data Acquisition Layer
        ↓
Video + Audio Analysis
        ↓
Comment Sentiment Analysis
        ↓
Popularity Metrics Analysis
        ↓
Multimodal Feature Fusion
        ↓
Audience Reaction Prediction
        ↓
Recommendation Engine
        ↓
Dashboard / Analytical Report
```

---

## 👥 Team Members

We are a team of dedicated software engineers with a focus on IoT and healthcare solutions:

| **IT Number**  | **Name**                 |
|----------------|--------------------------|
| IT22110152 | SALGADO M.B.U        |
| IT22236296 | DE SILVA T.R.R  |
| IT22189462 | SAMPATH P.D.D.I   |
| IT22347480 | HIMASHA Y.H.P      |

---

