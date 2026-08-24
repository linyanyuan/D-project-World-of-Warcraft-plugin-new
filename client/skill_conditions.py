"""
Reconstructed API stub from Nirvana30 Nuitka runtime metadata.
NOTE: Bodies are not recovered (Nuitka native). Signatures/locals come from co_varnames.
"""
from __future__ import annotations

from typing import Any

# original_file: D:\project\Nirvana30\Nirvana30\skill_conditions.py

# --- recovered constants ---
ConditionType = {"CONDITION_GROUP": "条件组", "HP_CONDITION": "血量判断", "BUFF_CONDITION": "光环判断", "ENEMY_COUNT": "敌方数量", "ALLY_HP_COUNT": "友方血量人数", "ALLY_BUFF_COUNT": "友方光环数量", "SKILL_CD": "技能CD", "PLAYER_INFO": "玩家信息", "TARGET_INFO": "目标信息", "FOCUS_INFO": "焦点信息", "BURST_TOGGLE": "爆发开关", "FORCE_COOLDOWN": "强制冷却", "ALLY_ROLE": "队友职责", "ALLY_DISPEL": "队友驱散"}
TargetType = {"TARGET": "目标", "FOCUS": "焦点", "SELF": "自己", "PARTY": "队友"}
ComparisonOperator = {"LESS_THAN": "小于", "GREATER_THAN": "大于", "EQUAL": "等于", "LESS_EQUAL": "小于等于", "GREATER_EQUAL": "大于等于"}
AuraConditionType = {"EXISTS": "存在", "NOT_EXISTS": "不存在", "DURATION": "持续时间", "STACKS": "层数", "ELAPSED": "已持续时间"}
ResourceType = {"Mana": [0, "法力值"], "Rage": [1, "怒气"], "Focus": [2, "集中值"], "Energy": [3, "能量"], "ComboPoints": [4, "连击点"], "Runes": [5, "符文"], "RunicPower": [6, "符文能量"], "SoulShards": [7, "灵魂碎片"], "LunarPower": [8, "星界能量"], "HolyPower": [9, "神圣能量"], "Alternate": [10, "特殊能量"], "Maelstrom": [11, "漩涡值"], "Chi": [12, "真气"], "Insanity": [13, "狂乱值"], "BurningEmbers": [14, "燃烧余烬（废弃）"], "DemonicFury": [15, "恶魔之怒（废弃）"], "ArcaneCharges": [16, "奥术充能"], "Fury": [17, "恶魔之怒"], "Pain": [18, "痛苦值"], "Essence": [19, "精华"], "WinePool": [30, "酒池"], "OverloadCharge": [31, "超荷充能"]}
PlayerInfoField = {"COMBAT": ["in_combat", "战斗状态", "bool"], "MOVING": ["is_moving", "移动状态", "bool"], "DEAD": ["is_dead", "死亡/幽灵", "bool"], "OUTDOORS": ["is_outdoors", "户外", "bool"], "IN_INSTANCE": ["in_instance", "副本内", "bool"], "CAN_PICKUP": ["can_pickup", "可交互", "bool"], "CAN_SWITCH_TARGET": ["can_switch_target", "可切换目标", "bool"], "IN_GROUP": ["in_group", "队伍状态", "number"], "LAST_SPELL_ID": ["last_spell_id", "上次施法ID", "number"], "CASTING_SPELL_ID": ["casting_spell_id", "当前施法ID", "number"], "CASTING_PROGRESS": ["casting_progress", "当前施法剩余时间", "number"], "CASTING_ELAPSED": ["casting_elapsed", "已施法时间", "number"], "RESOURCE": ["resource", "资源值", "resource"]}
TargetInfoField = {"COMBAT": ["in_combat", "战斗状态", "bool"], "MOVING": ["is_moving", "移动状态", "bool"], "DEAD": ["is_dead", "死亡状态", "bool"], "FRIENDLY": ["is_friendly", "友方判断", "bool"], "DISTANCE": ["distance", "距离", "number"], "UNIT_TYPE": ["unit_type", "目标类型", "number"]}

def _apply_negate(*args: Any, **kwargs: Any) -> Any:
    """co_varnames=['cond', 'ok']"""
    # co_names=['RuntimeError']
    raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

def _cmp(*args: Any, **kwargs: Any) -> Any:
    """co_varnames=['op', 'a', 'b']"""
    # co_names=['RuntimeError']
    raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

def _normalize_icon_confidence(*args: Any, **kwargs: Any) -> Any:
    """co_varnames=['raw', 'default', 'v']"""
    # co_names=['RuntimeError']
    raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

def _normalize_target_value(*args: Any, **kwargs: Any) -> Any:
    """co_varnames=['raw', 'default', 't']"""
    # co_names=['RuntimeError']
    raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

def evaluate_condition(*args: Any, **kwargs: Any) -> Any:
    """co_varnames=['cond', 'state', 'alive_ratios', 'owners', 'ctype', 'p', 'header', 'children', 'child_conditions', 'mode', 'checks', 'want', 'actual', '_dur_en', '_op', '_val', '_dur_field', 'op', 'value', 'want_group', 'actual_group', 'want_last_spell_id', 'actual_last_spell_id', 'want_casting_spell_id', 'actual_casting_spell_id', 'actual_progress', 'actual_elapsed', 'actual_pet', 'actual_hp', 'resource_index', 'resources', 'actual_value', 'rt', 'k', 'v', 'ki', 'has_focus', 'want_exists', 'want_interruptible', 'actual_interruptible', 'dist', 'cast_progress', 'target_is_dead', 'target_is_friendly', 'target_status', 'target_exists', 'has_target', 'actual_friend_enemy', 'actual_type', 'burst_type', 'burst_on', 'minor_on', 'selected_owner', 'target_scope', 'hp', 'info', 'actual_role', 'expected_role', 'expected_dt', 'dispel_mask', '_DISPEL_TO_BIT', 'actual_dispel', '_DISPEL_TO_INT', 'enemy_count', 'count', 'cd_by_id', 'skill_id', 'sid', 'cd', 'metric', 'actual_count', 'expect_count', 'bool_val', 'remain_s', 'cd_seconds', 'threshold_s', 'want_usable', 'unusable_flag', 'eta_raw', 'is_usable_now', 'eta_s', 'team_type', 'hp_percent', 'count_op', 'count_val', 'owner', 'ratio', 'ratio_f', 'threshold_ratio', 'matched', 'buff_id', 'include_self', 'buffs', 'player_info', 'party_owners', 'raid_owners', 'items', 'found', 'target', 'cond_type', 'found_conf', 'it', '_hit', 'current_conf', 'conf_op', 'expect_conf', 'fill_ratio', 'fill_px', 'raw_duration', 'duration_ratio', 'required', 'elapsed_s', 'target_elapsed']"""
    # co_names=['RuntimeError']
    raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

def evaluate_conditions(*args: Any, **kwargs: Any) -> Any:
    """co_varnames=['conditions', 'state', 'mode', 'c']"""
    # co_names=['RuntimeError']
    raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

def should_allow_skill_while_player_casting(*args: Any, **kwargs: Any) -> Any:
    """co_varnames=['conditions', 'state', 'mode', 'casting_conditions', '_collect_casting_conditions', 'raw', 'cond', 'params']"""
    # co_names=['RuntimeError']
    raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

class PlayerInfoField:
    def __init__(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['self', 'field_id', 'display_name', 'field_type']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')


class ResourceType:
    def __init__(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['self', 'index', 'display_name']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

    def get_by_index(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['cls', 'index', 'rt']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

    def get_display_name_by_index(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['cls', 'index', 'rt']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')


class SkillCondition:
    def __init__(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['self', 'condition_type', '_compat_map']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

    def _get_ally_buff_count_description(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['self', 'buff_id', 'buff_name', 'operator', 'count', 'include_self', 'id_display', 'self_text']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

    def _get_ally_dispel_description(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['self', '_DISPEL_NAMES', 'dt']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

    def _get_ally_hp_count_description(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['self', 'operator', 'hp_percent', 'count_operator', 'count']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

    def _get_ally_role_description(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['self', 'role', 'scope', 'role_map', 'scope_text']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

    def _get_buff_description(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['self', 'target', 'buff_id', 'buff_name', 'condition', 'id_display', 'desc', 'duration', 'duration_operator', 'elapsed', 'elapsed_operator', 'stack_count', 'stack_operator', 'conf_op', 'conf_val']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

    def _get_combat_description(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['self', 'target', 'in_combat', 'state']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

    def _get_enemy_count_description(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['self', 'operator', 'count']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

    def _get_focus_info_description(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['self', 'parts', 'val', 'state_text', 'operator', 'value']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

    def _get_hp_description(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['self', 'target', 'operator', 'value']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

    def _get_player_info_description(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['self', 'parts', 'val', 'state_text', '_dur_en', '_op', '_v', 'operator', 'value', 'group_type', '_group_names', 'resource_index', 'resource_name', 'pet_op', 'pet_val']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

    def _get_skill_cd_description(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['self', 'skill_id', 'skill_name', 'operator', 'metric', 'cd_time', 'charge_count', 'require_highlight', 'display', 'desc', 'bool_val', 'threshold', 'state_text']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

    def _get_target_info_description(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['self', 'parts', 'val', 'state_text', '_dur_en', '_op', '_v', 'operator', 'value', 'status', 'mapping', '_unit_type_names', 'type_name']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

    def from_dict(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['data', 'ctype', 'params', 'condition']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

    def get_description(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['self', 'prefix', 'name', 'match_mode', 'match_label', 'child_count', 'enabled', 'burst_type', 'burst_label', '_p', '_cd_raw', 'has_cd', 'cooldown', '_ws_raw', 'wait_s', 'wait_ms', 'parts']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

    def to_dict(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['self', 'children', 'child']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')


class SkillConditionManager:
    def conditions_to_dict_list(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['conditions']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

    def create_ally_hp_count_condition(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['operator', 'hp_percent', 'count_operator', 'count', 'condition']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

    def create_buff_condition(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['target', 'buff_id', 'condition_type', 'duration', 'duration_operator', 'buff_name', 'stack_count', 'stack_operator', 'elapsed_duration', 'elapsed_duration_operator', 'icon_confidence_enabled', 'icon_confidence_operator', 'icon_confidence', 'condition']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

    def create_combat_condition(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['target', 'in_combat', 'condition']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

    def create_enemy_count_condition(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['operator', 'count', 'condition']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

    def create_focus_info_condition(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['kwargs', 'condition']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

    def create_force_cooldown_condition(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['cooldown', 'condition']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

    def create_hp_condition(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['target', 'operator', 'value', 'condition']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

    def create_player_info_condition(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['kwargs', 'condition']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

    def create_skill_cd_condition(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['skill_id', 'operator', 'cd_time', 'skill_name', 'condition']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

    def create_skill_charges_condition(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['skill_id', 'operator', 'charge_count', 'skill_name', 'condition']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

    def create_target_info_condition(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['kwargs', 'condition']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

    def dict_list_to_conditions(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['data']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')

    def validate_conditions(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['conditions', 'condition']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')


class TargetInfoField:
    def __init__(*args: Any, **kwargs: Any) -> Any:
        """co_varnames=['self', 'field_id', 'display_name', 'field_type']"""
        # co_names=['RuntimeError']
        raise NotImplementedError('Nuitka-compiled in original Nirvana.exe')


