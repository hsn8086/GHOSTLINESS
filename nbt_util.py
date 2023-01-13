import copy

from nbt.nbt import *

from data_types import *


def dict2nbt(name, dict_: dict):
    return dict2tag_compound(dict_, True, name)


def dict2tag_compound(dict_: dict, is_top: bool = False, name: str = None):
    if name is None:
        name_ = ''
    else:
        name_ = copy.copy(name)

    if is_top:
        nbt = NBT()
        # nbt.name = name_
    else:
        nbt = TAG_Compound(name=name_)

    for key in dict_:
        value = dict_[key]
        type_ = type(value)
        nbt.tags.append(transform(key, value))
    return nbt


def transform(name, value):
    if name is None:
        name = ''
    type_ = type(value)
    if type_ in [Byte, bool]:
        return TAG_Byte(Byte(value), name)
    elif type_ == Short:
        return TAG_Short(value, name)
    elif type_ == int:
        return TAG_Int(value, name)
    elif type_ == Long:
        return TAG_Long(value, name)
    elif type_ == float:
        return TAG_Float(value, name)
    elif type_ == Double:
        return TAG_Double(value, name)
    elif type_ == ByteArray:
        return TAG_Byte_Array(value, name)
    elif type_ == str:
        return TAG_String(value, name)
    elif type_ == list:
        return list2tag_list(value, name)
    elif type_ == dict:
        return dict2tag_compound(value, name=name)
    elif type_ == list and type(value[0]) == int:
        return list2tag_list(value, name, TAG_Int_Array)
    elif type_ == list and type(value[0]) == Long:
        return list2tag_list(value, name, TAG_Long_Array)
    else:
        return TAG(value, name)


def list2tag_list(value, name: str = None, type_=None):
    if type_ is None:
        nbt = TAG_List(get_type(type(value[0])), name=name)
    else:
        nbt = type_(name)

    if name is None:
        name_ = ''
    else:
        name_ = copy.copy(name)
    [nbt.append(transform(None, v)) for v in value]
    return nbt


def get_type(type_=None, add_type=None):
    tl = {bool: TAG_Byte, Byte: TAG_Byte, Short: TAG_Short, int: TAG_Int, Long: TAG_Long, float: TAG_Float,
          Double: TAG_Double, ByteArray: TAG_Byte_Array, str: TAG_String, list: TAG_List, dict: TAG_Compound, None: TAG}
    t = tl[type_]
    if add_type == int:
        t = TAG_Int_Array
    elif add_type == Long:
        t = TAG_Long_Array
    return t
