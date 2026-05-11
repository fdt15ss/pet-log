from __future__ import annotations

from typing import Literal, TypeAlias

RecordCategory: TypeAlias = Literal["meal", "walk", "stool", "medical", "behavior"]
RecordStatus: TypeAlias = Literal["normal", "notice", "alert"]
RecordInputSource: TypeAlias = Literal["manual", "voice", "ai_preview", "quick_action"]
InsightSeverity: TypeAlias = Literal["info", "notice", "alert"]
ConversationMode: TypeAlias = Literal["care_question", "pet_chat"]
FilePurpose: TypeAlias = Literal["profile_photo", "record_attachment", "product_image"]
CommunityBoard: TypeAlias = Literal["유기동물", "용품 나눔", "자유게시판", "행동 고민", "후기"]
CommunityFeed: TypeAlias = Literal["인기글", "최신글", "내 주변"]
CommunityReactionType: TypeAlias = Literal["like"]
