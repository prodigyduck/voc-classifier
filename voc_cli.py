#!/usr/bin/env python3
import argparse
import requests
import sys
from pathlib import Path

API_BASE_URL = "http://localhost:8000/api/v1"


def create_voc(title, content, category_id, priority, submitted_by, ui_related):
    payload = {
        "title": title,
        "content": content,
        "category_id": category_id,
        "priority": priority,
        "submitted_by": submitted_by,
        "ui_related": ui_related
    }

    try:
        response = requests.post(f"{API_BASE_URL}/vocs", json=payload)
        if response.status_code == 201:
            result = response.json()
            print(f"✅ VOC가 등록되었습니다 (ID: {result['id']})")
            return result
        else:
            print(f"❌ 등록 실패: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return None


def list_vocs(category_id, status, priority, ui_related, limit):
    params = {}
    if category_id:
        params["category_id"] = category_id
    if status:
        params["status"] = status
    if priority:
        params["priority"] = priority
    if ui_related is not None:
        params["ui_related"] = ui_related
    if limit:
        params["limit"] = limit

    try:
        response = requests.get(f"{API_BASE_URL}/vocs", params=params)
        if response.status_code == 200:
            vocs = response.json()
            print(f"\n📋 VOC 목록 (총 {len(vocs)}건)\n")
            for voc in vocs:
                print(f"[{voc['id']}] {voc['title']}")
                print(f"    상태: {voc['status']} | 우선순위: {voc['priority']} | UI 관련: {'✅' if voc['ui_related'] else '❌'}")
                print(f"    제출자: {voc['submitted_by']} | 생성일: {voc['created_at']}\n")
            return vocs
        else:
            print(f"❌ 조회 실패: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return None


def train_classifier():
    print("📚 모델 학습 시작...")
    try:
        response = requests.post(f"{API_BASE_URL}/classification/train")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {result['message']}")
            return result
        else:
            print(f"❌ 학습 실패: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return None


def classify_voc(voc_id):
    print(f"🤖 VOC {voc_id} 분류 시작...")
    try:
        response = requests.post(f"{API_BASE_URL}/classification/classify/{voc_id}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 분류 완료")
            print(f"    제안 카테고리: {result['suggested_category']}")
            print(f"    신뢰도: {result['confidence_score']:.2f}")
            return result
        else:
            print(f"❌ 분류 실패: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return None


def classify_batch(limit):
    print(f"🤖 일괄 분류 시작 (최대 {limit}건)...")
    try:
        response = requests.post(f"{API_BASE_URL}/classification/classify-batch", params={"limit": limit})
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {result['message']}")
            return result
        else:
            print(f"❌ 분류 실패: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return None


def get_analytics():
    print("📊 분석 데이터 조회...")
    try:
        response = requests.get(f"{API_BASE_URL}/analytics/overview")
        if response.status_code == 200:
            data = response.json()
            print(f"\n📈 VOC 분석 개요\n")
            print(f"    전체 VOC: {data['total_vocs']}")
            print(f"    UI 관련 VOC: {data['ui_related_count']}")
            print(f"\n    카테고리별 분포:")
            for cat, count in data['by_category'].items():
                print(f"      - {cat}: {count}")
            print(f"\n    상태별 분포:")
            for status, count in data['by_status'].items():
                print(f"      - {status}: {count}")
            return data
        else:
            print(f"❌ 조회 실패: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return None


def main():
    parser = argparse.ArgumentParser(description="VOC Classifier CLI")
    subparsers = parser.add_subparsers(dest="command", help="명령어")

    create_parser = subparsers.add_parser("create", help="새 VOC 생성")
    create_parser.add_argument("--title", required=True, help="VOC 제목")
    create_parser.add_argument("--content", required=True, help="VOC 내용")
    create_parser.add_argument("--category-id", type=int, help="카테고리 ID")
    create_parser.add_argument("--priority", choices=["LOW", "MEDIUM", "HIGH", "CRITICAL"], default="MEDIUM", help="우선순위")
    create_parser.add_argument("--submitted-by", help="제출자")
    create_parser.add_argument("--ui-related", action="store_true", help="UI 개선 가능 여부")

    list_parser = subparsers.add_parser("list", help="VOC 목록 조회")
    list_parser.add_argument("--category-id", type=int, help="카테고리 ID 필터")
    list_parser.add_argument("--status", choices=["PENDING", "ANALYZED", "RESOLVED", "REJECTED"], help="상태 필터")
    list_parser.add_argument("--priority", choices=["LOW", "MEDIUM", "HIGH", "CRITICAL"], help="우선순위 필터")
    list_parser.add_argument("--ui-related", action="store_true", help="UI 관련만 표시")
    list_parser.add_argument("--limit", type=int, help="최대 표시 개수")

    subparsers.add_parser("train", help="분류 모델 학습")

    classify_parser = subparsers.add_parser("classify", help="VOC 분류")
    classify_parser.add_argument("--voc-id", type=int, help="분류할 VOC ID")
    classify_parser.add_argument("--batch", action="store_true", help="일괄 분류")
    classify_parser.add_argument("--limit", type=int, default=100, help="일괄 분류 시 최대 개수")

    subparsers.add_parser("analytics", help="분석 데이터 조회")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "create":
        create_voc(
            title=args.title,
            content=args.content,
            category_id=args.category_id,
            priority=args.priority,
            submitted_by=args.submitted_by,
            ui_related=args.ui_related
        )
    elif args.command == "list":
        list_vocs(
            category_id=args.category_id,
            status=args.status,
            priority=args.priority,
            ui_related=args.ui_related,
            limit=args.limit
        )
    elif args.command == "train":
        train_classifier()
    elif args.command == "classify":
        if args.batch:
            classify_batch(args.limit)
        elif args.voc_id:
            classify_voc(args.voc_id)
        else:
            print("❌ --voc-id 또는 --batch 옵션이 필요합니다.")
    elif args.command == "analytics":
        get_analytics()


if __name__ == "__main__":
    main()
