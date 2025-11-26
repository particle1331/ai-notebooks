import flet as ft
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from enum import Enum

# =============================================================================
# DATA MODELS
# =============================================================================

CHAT_WIDTH = 800

@dataclass
class MessageData:
    """Data model for a single conversation message"""
    text: str
    is_user: bool
    timestamp: Optional[float] = None
    msg_id: Optional[int] = None

@dataclass  
class AnnotationData:
    """Data model for conversation annotations"""
    annotation_id: int
    text: str
    message_indices: List[int]

class BlockType(Enum):
    """Types of conversation blocks"""
    ANNOTATED_GROUP = "annotated_group"
    INDIVIDUAL_MESSAGE = "individual_message"

class ColorTheme:
    """Centralized color management"""
    PRIMARY_BLUE = '#1E40AF'
    WHITE = '#FFFFFF'
    TEAL = '#0F766E'
    TEAL_GREEN = '#059669'
    ORANGE = '#F7A51A'
    LIGHT_GRAY = '#F8FAFC'
    MEDIUM_GRAY = '#E2E8F0'
    DARK_GRAY = '#475569'
    TEXT_DARK = '#1E293B'
    HIGHLIGHT_BG = '#F7A51A'
    HIGHLIGHT_BORDER = '#F7A51A'
    ANNOTATION_BG = '#F0FDF4'
    ANNOTATION_BORDER = '#059669'
    
    USER_BUBBLE = PRIMARY_BLUE
    AGENT_BUBBLE = MEDIUM_GRAY
    USER_TEXT = WHITE
    AGENT_TEXT = TEXT_DARK

# =============================================================================
# UTILITIES
# =============================================================================

class TimeFormatter:
    """Utility class for timestamp formatting"""
    
    @staticmethod
    def format_timestamp(seconds: Optional[float]) -> str:
        if seconds is None:
            return "—:—"
        
        if seconds < 3600:
            minutes = int(seconds // 60)
            seconds_remaining = int(seconds % 60)
            return f"{minutes:02d}:{seconds_remaining:02d}"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            seconds_remaining = int(seconds % 60)
            return f"{hours:02d}:{minutes:02d}:{seconds_remaining:02d}"

class ConversationBlockFactory:
    """Factory for creating different types of conversation blocks"""
    
    @staticmethod
    def create_message_bubble(message_data: MessageData) -> ft.Container:
        time_str = TimeFormatter.format_timestamp(message_data.timestamp)
        
        if message_data.is_user:
            bubble_config = BubbleConfig(
                bg_color=ColorTheme.USER_BUBBLE,
                text_color=ColorTheme.USER_TEXT,
                alignment=ft.MainAxisAlignment.END
            )
        else:
            bubble_config = BubbleConfig(
                bg_color=ColorTheme.AGENT_BUBBLE, 
                text_color=ColorTheme.AGENT_TEXT,
                alignment=ft.MainAxisAlignment.START
            )
        
        return MessageBubbleCreator.create_bubble(
            text=message_data.text,
            timestamp=time_str,
            config=bubble_config
        )

@dataclass
class BubbleConfig:
    bg_color: str
    text_color: str
    alignment: ft.MainAxisAlignment

class MessageBubbleCreator:
    """Creates message bubble widgets with consistent styling"""
    
    @staticmethod
    def create_bubble(text: str, timestamp: str, config: BubbleConfig) -> ft.Container:

        timestamp_widget = ft.Container(
            content=ft.Text(timestamp, size=10, color=ColorTheme.DARK_GRAY),
            width=80,
            alignment=ft.alignment.center
        )
        
        bubble = ft.Container(
            content=ft.Text(text, color=config.text_color, selectable=True, size=14),
            padding=ft.padding.all(12),
            bgcolor=config.bg_color,
            border_radius=15,
            expand=False,          # <<< ADDED
            width=450,             # <<< ADDED (max bubble width)
        )
        
        return ft.Row(
            controls=[
                timestamp_widget,
                ft.Container(
                    content=bubble,
                    expand=True,
                    alignment=ft.alignment.center_left if config.alignment == ft.MainAxisAlignment.START else ft.alignment.center_right
                )
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
            spacing=10
        )

# =============================================================================
# CONVERSATION BLOCKS
# =============================================================================

class Highlightable:
    def __init__(self):
        self.is_highlighted = False
        self._original_border = None
    
    def highlight(self, border_color: str = ColorTheme.HIGHLIGHT_BORDER):
        if hasattr(self, 'container'):
            self._original_border = self.container.border
            self.container.border = ft.border.all(3, border_color)
            self.is_highlighted = True
            self.container.update()
    
    def unhighlight(self):
        if hasattr(self, 'container') and self._original_border:
            self.container.border = self._original_border
            self.is_highlighted = False
            self.container.update()

class BaseConversationBlock(Highlightable):
    def __init__(self):
        super().__init__()
        self.container = None
    
    @property
    def control(self) -> ft.Control:
        return self.container

class AnnotatedMessageGroup(BaseConversationBlock):
    """A group of messages under a single annotation"""
    
    def __init__(self, annotation: AnnotationData, messages: List[MessageData]):
        super().__init__()
        self.annotation = annotation
        self.messages = self._filter_messages(messages, annotation.message_indices)
        self._create_container()
    
    def _filter_messages(self, messages: List[MessageData], indices: List[int]) -> List[MessageData]:
        return [messages[i] for i in indices if i < len(messages)]
    
    def _create_container(self):
        self.container = ft.Container(
            bgcolor=ColorTheme.LIGHT_GRAY,
            border=ft.border.all(2, ColorTheme.LIGHT_GRAY),
            border_radius=12,
            padding=10,
            margin=ft.margin.only(bottom=10),
            content=self._create_content(),
            key=f"annotated_block_{self.annotation.annotation_id}"
        )
    
    def _create_content(self) -> ft.Column:
        return ft.Column(
            controls=[
                self._create_annotation_header(),
                self._create_annotation_content(),
                self._create_messages_section()
            ],
            spacing=0
        )
    
    def _create_annotation_header(self) -> ft.Container:
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.LIGHTBULB_OUTLINED, size=16, color=ColorTheme.TEAL_GREEN),
                    ft.Text(
                        f"Coaching Tip #{self.annotation.annotation_id}", 
                        size=12, 
                        color=ColorTheme.TEAL_GREEN, 
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Container(expand=True),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.all(12),
            bgcolor=ColorTheme.ANNOTATION_BG,
            border=ft.border.only(
                bottom=ft.border.BorderSide(2, ColorTheme.ANNOTATION_BORDER)
            ),
        )
    
    def _create_annotation_content(self) -> ft.Container:
        return ft.Container(
            content=ft.Text(self.annotation.text, size=14, selectable=True),
            padding=ft.padding.all(12),
            bgcolor=ColorTheme.ANNOTATION_BG,
            expand=True,
            alignment=ft.alignment.center_left
        )
    
    def _create_messages_section(self) -> ft.Container:
        messages_column = ft.Column(spacing=8)
        
        for message_data in self.messages:
            message_bubble = ConversationBlockFactory.create_message_bubble(message_data)
            messages_column.controls.append(message_bubble)
        
        return ft.Container(
            content=messages_column,
            padding=ft.padding.all(12),
            bgcolor=ColorTheme.LIGHT_GRAY
        )

class IndividualMessage(BaseConversationBlock):
    """A single message without annotation"""
    
    def __init__(self, message_data: MessageData, message_index: int):
        super().__init__()
        self.message_data = message_data
        self.message_index = message_index
        self._create_container()
    
    def _create_container(self):
        self.container = ft.Container(
            bgcolor=ColorTheme.LIGHT_GRAY,
            border=ft.border.all(2, ColorTheme.LIGHT_GRAY),
            border_radius=8,
            padding=15,
            margin=ft.margin.only(bottom=5),
            content=ConversationBlockFactory.create_message_bubble(self.message_data),
            key=f"individual_msg_{self.message_index}"
        )

# =============================================================================
# CONVERSATION MANAGEMENT
# =============================================================================

class ConversationManager:
    """Manages conversation data, annotations, and flow construction"""
    
    def __init__(self):
        self.messages: List[MessageData] = []
        self.annotations: List[AnnotationData] = []
        self.annotation_counter = 0
    
    def add_message(self, text: str, is_user: bool = False, timestamp: Optional[float] = None) -> int:
        message_data = MessageData(
            text=text,
            is_user=is_user,
            timestamp=timestamp,
            msg_id=len(self.messages)
        )
        self.messages.append(message_data)
        return message_data.msg_id
    
    def add_annotation(self, text: str, message_indices: List[int]) -> int:
        self.annotation_counter += 1
        annotation = AnnotationData(
            annotation_id=self.annotation_counter,
            text=text,
            message_indices=sorted(message_indices)
        )
        self.annotations.append(annotation)
        return annotation.annotation_id
    
    def get_conversation_flow(self) -> List[BaseConversationBlock]:
        used_message_indices = set()
        conversation_blocks = []
        
        annotated_groups = self._create_annotated_groups(used_message_indices)
        
        return self._interleave_blocks(annotated_groups, used_message_indices)
    
    def _create_annotated_groups(self, used_message_indices: set) -> List[AnnotatedMessageGroup]:
        groups = []
        for annotation in self.annotations:
            group = AnnotatedMessageGroup(annotation, self.messages)
            groups.append(group)
            used_message_indices.update(annotation.message_indices)
        
        return sorted(groups, key=lambda group: group.annotation.message_indices[0])
    
    def _interleave_blocks(self, annotated_groups: List[AnnotatedMessageGroup], 
                          used_message_indices: set) -> List[BaseConversationBlock]:
        blocks = []
        current_index = 0
        group_index = 0
        
        while current_index < len(self.messages):
            if self._should_add_annotated_group(annotated_groups, group_index, current_index):
                blocks.append(annotated_groups[group_index])
                current_index = self._get_next_index_after_group(annotated_groups[group_index])
                group_index += 1
            else:
                if current_index not in used_message_indices:
                    blocks.append(IndividualMessage(self.messages[current_index], current_index))
                current_index += 1
        
        return blocks
    
    def _should_add_annotated_group(self, groups: List[AnnotatedMessageGroup], 
                                  group_index: int, current_index: int) -> bool:
        return (group_index < len(groups) and 
                groups[group_index].annotation.message_indices[0] == current_index)
    
    def _get_next_index_after_group(self, group: AnnotatedMessageGroup) -> int:
        return max(group.annotation.message_indices) + 1

# =============================================================================
# NAVIGATION COMPONENTS
# =============================================================================

class NavigationPanel(ft.Container):
    """Navigation panel"""

    def __init__(self, conversation_blocks: List[BaseConversationBlock], 
                 main_column: ft.Column, conversation_manager: ConversationManager):
        super().__init__()
        self.conversation_blocks = conversation_blocks
        self.main_column = main_column
        self.conversation_manager = conversation_manager
        self.current_annotation_index = -1
        
        self._setup_panel_styling()
        self._create_ui_components()
        self._assemble_panel()
    
    def _setup_panel_styling(self):
        self.width = 60
        self.padding = 10
        self.bgcolor = ColorTheme.LIGHT_GRAY
        self.border_radius = 8
    
    def _create_ui_components(self):
        self.indicators_column = ft.Column(
            scroll=ft.ScrollMode.ADAPTIVE,
            height=300,
            spacing=2
        )
        
        self.counter_text = ft.Text("0/0", size=10, color=ColorTheme.DARK_GRAY)
        self.position_text = ft.Text("--", size=12, weight=ft.FontWeight.BOLD, color=ColorTheme.PRIMARY_BLUE)
    
    def _assemble_panel(self):
        self.content = ft.Column(
            controls=[
                self._create_logo_section(),
                ft.Divider(height=10),
                self._create_navigation_controls(),
                ft.Divider(height=10),
                self._create_flow_indicators_section(),
            ],
            spacing=5,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    
    def _create_logo_section(self) -> ft.Control:
        return ft.Image(
            src="afni.jpeg",
            width=60,
            height=60,
            fit=ft.ImageFit.CONTAIN,
        )
    
    def _create_navigation_controls(self) -> ft.Control:
        return ft.Column(
            controls=[
                self._create_nav_button(ft.Icons.ARROW_UPWARD, ColorTheme.TEAL, self.previous_note),
                ft.Container(content=self.position_text, alignment=ft.alignment.center, padding=5),
                self._create_nav_button(ft.Icons.ARROW_DOWNWARD, ColorTheme.TEAL_GREEN, self.next_note),
            ],
            spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    
    def _create_nav_button(self, icon: str, color: str, on_click_handler) -> ft.Container:
        return ft.Container(
            content=ft.IconButton(
                icon=icon,
                icon_size=16,
                on_click=on_click_handler,
                style=ft.ButtonStyle(color=ColorTheme.WHITE, bgcolor=color, padding=8),
            ),
            alignment=ft.alignment.center,
        )
    
    def _create_flow_indicators_section(self) -> ft.Control:
        return ft.Container(
            content=ft.Column([
                ft.Text("  Flow", size=8, color=ColorTheme.DARK_GRAY),
                self.indicators_column
            ], spacing=2),
            padding=5,
        )
    
    def initialize_indicators(self):
        self._update_indicators()
    
    def _update_indicators(self):
        self.indicators_column.controls.clear()
        
        for i, block in enumerate(self.conversation_blocks):
            indicator = self._create_block_indicator(block, i)
            self.indicators_column.controls.append(
                ft.Container(content=indicator, alignment=ft.alignment.center, padding=2)
            )
        
        self._update_counter_display()
        self._update_position_display()
        self._refresh_ui()
    
    def _create_block_indicator(self, block: BaseConversationBlock, index: int) -> ft.Container:
        if isinstance(block, AnnotatedMessageGroup):
            return self._create_annotation_indicator(block, index)
        else:
            return self._create_message_indicator(block, index)
    
    def _create_annotation_indicator(self, block: AnnotatedMessageGroup, index: int) -> ft.Container:
        return ft.Container(
            content=ft.Text("■", size=10, color=ColorTheme.TEAL_GREEN, weight=ft.FontWeight.BOLD),
            on_click=lambda e, idx=index: self.jump_to_block(idx),
            tooltip=f"Coaching Tip #{block.annotation.annotation_id}",
        )
    
    def _create_message_indicator(self, block: IndividualMessage, index: int) -> ft.Container:
        return ft.Container(
            content=ft.Text("□", size=10, color=ColorTheme.DARK_GRAY),
            on_click=lambda e, idx=index: self.jump_to_block(idx),
            tooltip=f"Segment {block.message_index}",
        )
    
    def _update_counter_display(self):
        annotated_blocks = [b for b in self.conversation_blocks if isinstance(b, AnnotatedMessageGroup)]
        self.counter_text.value = f"{len(annotated_blocks)}/{len(self.conversation_blocks)}"
    
    def _update_position_display(self):
        annotated_blocks = [b for b in self.conversation_blocks if isinstance(b, AnnotatedMessageGroup)]
        
        if self.current_annotation_index >= 0 and annotated_blocks:
            current_pos = self.current_annotation_index + 1
            self.position_text.value = f"{current_pos}/{len(annotated_blocks)}"
        else:
            self.position_text.value = "--"
    
    def _refresh_ui(self):
        if hasattr(self, '_Control__page') and self._Control__page is not None:
            self.indicators_column.update()
            self.position_text.update()
    
    def _unhighlight_all_blocks(self):
        for block in self.conversation_blocks:
            block.unhighlight()
    
    def next_note(self, e):
        annotated_blocks = [b for b in self.conversation_blocks if isinstance(b, AnnotatedMessageGroup)]
        if not annotated_blocks:
            return
        
        self._unhighlight_all_blocks()
        self.current_annotation_index = (self.current_annotation_index + 1) % len(annotated_blocks)
        self._highlight_current_annotation(annotated_blocks)
    
    def previous_note(self, e):
        annotated_blocks = [b for b in self.conversation_blocks if isinstance(b, AnnotatedMessageGroup)]
        if not annotated_blocks:
            return
        
        self._unhighlight_all_blocks()
        self.current_annotation_index = (self.current_annotation_index - 1) % len(annotated_blocks)
        self._highlight_current_annotation(annotated_blocks)
    
    def _highlight_current_annotation(self, annotated_blocks: List[AnnotatedMessageGroup]):
        annotated_blocks[self.current_annotation_index].highlight()
        self._update_position_display()
        self.position_text.update()
        
        block_index = self.conversation_blocks.index(annotated_blocks[self.current_annotation_index])
        self._scroll_to_block(block_index)
    
    def jump_to_block(self, block_index: int):
        self._unhighlight_all_blocks()
        block = self.conversation_blocks[block_index]
        block.highlight()
        
        if isinstance(block, AnnotatedMessageGroup):
            self._update_annotation_position(block)
        else:
            self.current_annotation_index = -1
            self._update_position_display()
            self.position_text.update()
        
        self._scroll_to_block(block_index)
    
    def _update_annotation_position(self, block: AnnotatedMessageGroup):
        annotated_blocks = [b for b in self.conversation_blocks if isinstance(b, AnnotatedMessageGroup)]
        self.current_annotation_index = annotated_blocks.index(block)
        self._update_position_display()
        self.position_text.update()
    
    def _scroll_to_block(self, block_index: int):
        try:
            target_block = self.conversation_blocks[block_index]
            self.main_column.scroll_to(
                key=target_block.control.key,
                duration=400,
                curve=ft.AnimationCurve.EASE_OUT
            )
            self.main_column.update()
        except Exception:
            self._scroll_fallback(target_block)
    
    def _scroll_fallback(self, target_block: BaseConversationBlock):
        try:
            self.main_column.scroll_to(key=target_block.control.key, duration=0)
            self.main_column.update()
        except Exception:
            try:
                self.main_column.scroll_to(key=target_block.control.key)
                self.main_column.update()
            except Exception:
                pass

# =============================================================================
# MAIN APPLICATION
# =============================================================================

class SalesConversationAnalyzer:
    def __init__(self):
        self.conversation_manager = ConversationManager()
        self.main_column = None
        self.nav_panel = None
    
    def load_conversation(self, transcript: List[Dict], annotations: Optional[List[Dict]] = None):
        self.conversation_manager = ConversationManager()
        
        for msg_data in transcript:
            self.conversation_manager.add_message(
                text=msg_data['text'],
                is_user=msg_data.get('is_user', False),
                timestamp=msg_data.get('timestamp')
            )
        
        if annotations:
            for annotation_data in annotations:
                self.conversation_manager.add_annotation(
                    text=annotation_data['text'],
                    message_indices=annotation_data['message_indices']
                )
    
    def build_ui(self, page: ft.Page):
        self._setup_page_config(page)
        self._create_main_layout()
        page.add(self._create_main_container())
        
        self.nav_panel.initialize_indicators()
    
    def _setup_page_config(self, page: ft.Page):
        page.title = "Sales Conversation Analyzer"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.bgcolor = ColorTheme.WHITE
        page.padding = 20
    
    def _create_main_layout(self):
        self.main_column = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=5,
            expand=True,
        )
        
        conversation_blocks = self.conversation_manager.get_conversation_flow()
        self._populate_main_column(conversation_blocks)
        
        self.nav_panel = NavigationPanel(
            conversation_blocks, 
            self.main_column, 
            self.conversation_manager
        )
    
    def _populate_main_column(self, conversation_blocks: List[BaseConversationBlock]):
        for block in conversation_blocks:
            self.main_column.controls.append(block.control)
    
    def _create_main_container(self) -> ft.Row:
        return ft.Row(
            expand=True,
            controls=[
                # LEFT NAVIGATION COLUMN
                self.nav_panel,

                # RIGHT SIDE — CENTERED CHAT WITH MAX WIDTH
                ft.Container(
                    expand=True,
                    alignment=ft.alignment.top_left,
                    content=ft.Container(
                        width=CHAT_WIDTH,                     # <-- max width
                        alignment=ft.alignment.top_center,
                        content=self.main_column
                    ),
                ),
            ],
        )



def create_sample_data() -> tuple:
    transcript = [
        {"text": "Hi there! Thanks for making time to chat today.", "is_user": False, "timestamp": 0},
        {"text": "Hey! No problem, thanks for reaching out. Can you hear me alright?", "is_user": True, "timestamp": 60},
        {"text": "Yes, crystal clear! How's your day going so far?", "is_user": False, "timestamp": 120},
        {"text": "Pretty busy but good! We've got a lot going on with Q4 planning.", "is_user": True, "timestamp": 180},
        {"text": "I hear that - it's that time of year! I wanted to learn more about how your team currently handles sales training.", "is_user": False, "timestamp": 240},
        {"text": "Right now we do weekly team meetings and some ad-hoc coaching when we see issues.", "is_user": True, "timestamp": 300},
        {"text": "That makes sense. What kind of challenges are you noticing with that approach?", "is_user": False, "timestamp": 360},
        {"text": "Mainly consistency - different managers coach differently, and new hires take a while to get up to speed.", "is_user": True, "timestamp": 420},
        {"text": "Interesting. How long have you been using this approach?", "is_user": False, "timestamp": 480},
        {"text": "About two years now. It worked well when we were smaller, but with 45 reps it's becoming challenging.", "is_user": True, "timestamp": 540},
        {"text": "That's actually really common. We see many teams struggle with maintaining consistent messaging across different coaches.", "is_user": False, "timestamp": 600},
        {"text": "How do other companies handle this?", "is_user": True, "timestamp": 660},
        {"text": "Most successful teams use structured training with ongoing reinforcement and measurable outcomes.", "is_user": False, "timestamp": 720},
        {"text": "That sounds like what we need. Can you send me more information?", "is_user": True, "timestamp": 780},
        {"text": "Absolutely! I'll put together a detailed proposal and follow up tomorrow." * 3, "is_user": False, "timestamp": 840},
    ]
    
    annotations = [
        {
            "text": "Excellent opening - builds rapport naturally while establishing clear communication.",
            "message_indices": [0, 1, 2, 3]
        },
        {
            "text": "Strong discovery - identifies specific pain points.",
            "message_indices": [4, 5, 6, 7]
        },
        {
            "text": "Good transition to solution.",
            "message_indices": [8, 9, 10, 11]
        }
    ]
    
    return transcript, annotations

def main(page: ft.Page):
    transcript, annotations = create_sample_data()
    
    analyzer = SalesConversationAnalyzer()
    analyzer.load_conversation(transcript, annotations)
    analyzer.build_ui(page)

if __name__ == "__main__":
    ft.app(main, view=ft.WEB_BROWSER)
