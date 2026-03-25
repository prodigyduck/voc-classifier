from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
import yaml
from pathlib import Path
from typing import List, Dict, Tuple


class VOCClassifier:
    def __init__(self):
        config_path = Path(__file__).parent.parent.parent / "config.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        bertopic_config = self.config.get("bertopic", {})
        classification_config = self.config.get("classification", {})

        self.language = bertopic_config.get("language", "korean")
        self.model_name = bertopic_config.get("model_name", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        self.min_topic_size = bertopic_config.get("min_topic_size", 10)
        self.nr_topics = bertopic_config.get("nr_topics")
        self.calculate_probabilities = bertopic_config.get("calculate_probabilities", True)
        self.confidence_threshold = classification_config.get("confidence_threshold", 0.6)

        self.model = None
        self.embedding_model = None
        self._initialize_model()

    def _initialize_model(self):
        try:
            self.embedding_model = SentenceTransformer(self.model_name)

            self.model = BERTopic(
                language=self.language,
                embedding_model=self.embedding_model,
                min_topic_size=self.min_topic_size,
                nr_topics=self.nr_topics,
                calculate_probabilities=self.calculate_probabilities,
                verbose=True
            )
        except Exception as e:
            print(f"모델 초기화 중 오류 발생: {e}")
            raise

    def fit(self, documents: List[str]):
        if not documents:
            raise ValueError("분류할 문서가 없습니다.")

        topics, probs = self.model.fit_transform(documents)

        return topics, probs

    def predict(self, documents: List[str]) -> List[Dict]:
        if not self.model:
            raise RuntimeError("모델이 학습되지 않았습니다. 먼저 fit()을 호출하세요.")

        if not documents:
            return []

        topics, probs = self.model.transform(documents)

        results = []
        for i, (topic, prob) in enumerate(zip(topics, probs)):
            topic_info = self.model.get_topic(topic) if topic != -1 else []

            results.append({
                "topic_id": int(topic),
                "probability": float(prob[topic]) if len(prob) > topic else 0.0,
                "topic_keywords": topic_info if topic != -1 else [],
                "is_outlier": topic == -1,
                "document_index": i
            })

        return results

    def get_topic_info(self) -> List[Dict]:
        if not self.model:
            raise RuntimeError("모델이 학습되지 않았습니다.")

        topic_info = self.model.get_topic_info()
        result = []

        for _, row in topic_info.iterrows():
            topic_id = int(row["Topic"])
            if topic_id == -1:
                continue

            keywords = self.model.get_topic(topic_id)

            result.append({
                "topic_id": topic_id,
                "count": int(row["Count"]),
                "name": row["Name"],
                "keywords": keywords,
                "representative_docs": self.model.get_representative_docs(topic_id)
            })

        return result

    def suggest_category_name(self, keywords: List[Tuple[str, float]]) -> str:
        if not keywords:
            return "기타"

        top_keywords = [kw for kw, _ in keywords[:3]]

        keyword_str = ", ".join(top_keywords)

        common_patterns = {
            "오류": ["버그", "에러", "오류", "실패", "동작하지 않"],
            "UI": ["화면", "버튼", "메뉴", "인터페이스", "디자인", "표시"],
            "성능": ["느림", "지연", "속도", "로딩", "대기"],
            "기능": ["기능", "추가", "요청", "지원", "기능"],
            "데이터": ["데이터", "저장", "검색", "내보내기", "가져오기"],
            "보안": ["로그인", "권한", "인증", "접근", "보안"]
        }

        for category, patterns in common_patterns.items():
            for pattern in patterns:
                if pattern in keyword_str:
                    return category

        return f"{top_keywords[0]} 관련"

    def classify_voc(self, title: str, content: str) -> Dict:
        document = f"{title}. {content}"
        prediction = self.predict([document])

        if not prediction:
            return {
                "category": None,
                "confidence": 0.0,
                "topic_id": -1,
                "keywords": []
            }

        result = prediction[0]

        if result["is_outlier"]:
            return {
                "category": "기타",
                "confidence": 0.0,
                "topic_id": -1,
                "keywords": []
            }

        keywords = result["topic_keywords"]
        category = self.suggest_category_name(keywords)
        confidence = result["probability"]

        return {
            "category": category,
            "confidence": confidence,
            "topic_id": result["topic_id"],
            "keywords": [kw[0] for kw in keywords[:5]]
        }

    def batch_classify(self, voc_data: List[Dict]) -> List[Dict]:
        documents = [f"{voc['title']}. {voc['content']}" for voc in voc_data]

        predictions = self.predict(documents)

        results = []
        for i, prediction in enumerate(predictions):
            if prediction["is_outlier"]:
                results.append({
                    "voc_id": voc_data[i]["id"],
                    "category": "기타",
                    "confidence": 0.0,
                    "topic_id": -1,
                    "keywords": []
                })
            else:
                keywords = prediction["topic_keywords"]
                category = self.suggest_category_name(keywords)

                results.append({
                    "voc_id": voc_data[i]["id"],
                    "category": category,
                    "confidence": prediction["probability"],
                    "topic_id": prediction["topic_id"],
                    "keywords": [kw[0] for kw in keywords[:5]]
                })

        return results
