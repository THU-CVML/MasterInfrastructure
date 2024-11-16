"""Using Python dataclass and optuna distribution to define arguments of a function, in order to enable documentatable, easy and pythonic way to handle hyperparameters optimization."""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../notebooks/01_rv_args (arguments are random variables).ipynb.

# %% auto 0
__all__ = ['rv_dataclass_metadata_key', 'rv_missing_value', 'experiment_setting', 'PythonField', 'RandomVariable',
           'is_experiment_setting', 'show_dataframe_doc', 'get_optuna_search_space', 'optuna_suggest',
           'experiment_setting_decorator', 'pre_init_decorator', 'dataclass_for_torch_decorator', 'ExperimentModule']

# %% ../notebooks/01_rv_args (arguments are random variables).ipynb 4
from dataclasses import dataclass, field, MISSING, _MISSING_TYPE, fields, asdict
from typing import List, Dict, Any, Type, Optional, Callable, Union
from optuna.distributions import BaseDistribution, distribution_to_json, json_to_distribution

rv_dataclass_metadata_key = "thu_rv"
rv_missing_value = "thu_rv_missing"

@dataclass
class PythonField:
    default:Any = rv_missing_value# The default value of the field
    default_factory:Callable[[], Any] = rv_missing_value# A function to generate the default value of the field
    init:bool=True
    repr:bool=True
    hash:Union[None, bool]=None
    compare:bool=True
    metadata:Union[Dict[str, Any], None]=None
    # kw_only:Union[_MISSING_TYPE, bool]=MISSING
    kw_only:Union[None, bool]=rv_missing_value
    def __post_init__(self):
        # print(self)
        if self.default == rv_missing_value:
            self.default = MISSING
        if self.default_factory == rv_missing_value:
            self.default_factory = MISSING
        if self.kw_only == rv_missing_value:
            self.kw_only = MISSING
        # self.default = self.default or MISSING
        # self.default_factory = self.default_factory or MISSING
        # self.kw_only = self.kw_only or MISSING
    def __call__(self, **kwargs: Any) -> Any:
        if self.metadata is None:
            # self.metadata = {**kwargs}
            metadata = {**kwargs}
        
        return field(default=self.default, 
                     default_factory=self.default_factory, 
                     init=self.init, 
                     repr=self.repr, 
                     hash=self.hash, 
                     compare=self.compare, 
                     metadata=metadata, 
                     kw_only=self.kw_only)
    def __invert__(self):
        return self()

@dataclass
class RandomVariable(PythonField):
    description: str = "MISSING description. "# The description of the field
    distribution:BaseDistribution = "MISSING distribution. "# The distribution of the data
    def __call__(self, **kwargs: Any) -> Any:
        return super().__call__(description=self.description, distribution=self.distribution, 
                                **{rv_dataclass_metadata_key: self}, 
                                **kwargs)
    def __invert__(self):
        return self()

# %% ../notebooks/01_rv_args (arguments are random variables).ipynb 6
from decorator import decorator
from fastcore.basics import patch_to
from dataclasses import asdict
import pandas as pd
from optuna import Trial

def is_experiment_setting(cls):
    for field in fields(cls):
        if not isinstance(field.metadata.get(rv_dataclass_metadata_key, None), RandomVariable):
           return False
    return True
        
def show_dataframe_doc(cls):
    results = []
    for field in fields(cls):
        rv = field.metadata.get(rv_dataclass_metadata_key, None)
        if rv is None:
            raise ValueError("Class decorated with @experiment_setting needs to use ~RandomVariable fields. ")
        field_info = dict(name=field.name, type=field.type) | asdict(rv)
        results.append(field_info)
    return pd.DataFrame(results)


def get_optuna_search_space(cls, frozen_rvs:set = None):
    search_space = {}
    for field in fields(cls):
        field_name = field.name
        if frozen_rvs is not None and field_name in frozen_rvs:
            continue
        rv = field.metadata.get(rv_dataclass_metadata_key, None)
        if rv is None:
            raise ValueError("Class decorated with @experiment_setting needs to use ~RandomVariable fields. ")
        search_space[field_name] = rv.distribution
    return search_space

from copy import deepcopy
def optuna_suggest(cls:Type, trial:Trial, fixed_meta_params, suggest_params_only_in: set = None):
    suggested_params = deepcopy(fixed_meta_params)
    if suggest_only_in is None:
        suggest_only_in = set(field.name for field in fields(cls))
    # fixed_meta_params is dataclass
    if not isinstance(fixed_meta_params, cls):
        raise ValueError(f"fixed_meta_params should be an instance of the {cls.__name__} class.")
    for field in fields(cls):
        if field.name not in suggest_only_in:
            continue
        rv = field.metadata.get(rv_dataclass_metadata_key, None)
        if rv is None:
            raise ValueError("Class decorated with @experiment_setting needs to use ~RandomVariable fields. ")
        suggested_value = trial._suggest(field.name, rv.distribution)
        setattr(suggested_params, field.name, suggested_value)
    return suggested_params
    


@decorator
def experiment_setting_decorator(dataclass_func, *args, **kwargs):
    result_cls = dataclass_func(*args, **kwargs)
    if not is_experiment_setting(result_cls):
        raise ValueError("Class decorated with @experiment_setting needs to use ~RandomVariable fields. ")
    patch_to(result_cls, cls_method=True)(show_dataframe_doc)
    patch_to(result_cls, cls_method=True)(get_optuna_search_space)
    patch_to(result_cls, cls_method=True)(optuna_suggest)
    return result_cls

experiment_setting = experiment_setting_decorator(dataclass)

# %% ../notebooks/01_rv_args (arguments are random variables).ipynb 13
@decorator
def pre_init_decorator(init_func, self, *args, **kwargs):
    self.__pre_init__(*args, **kwargs)
    return init_func(self, *args, **kwargs)

# %% ../notebooks/01_rv_args (arguments are random variables).ipynb 15
def dataclass_for_torch_decorator(dataclass_func):
    def wrapped_func(cls):
        result_cls = dataclass_func(cls, eq=False) 
        result_cls.__init__ = pre_init_decorator(result_cls.__init__, self=cls) #TODO 非常奇怪，但是似乎测试逻辑是对的
        return cls
    return wrapped_func

# %% ../notebooks/01_rv_args (arguments are random variables).ipynb 16
_experiment_module = dataclass_for_torch_decorator(experiment_setting) # 隐藏，不建议直接使用

# %% ../notebooks/01_rv_args (arguments are random variables).ipynb 17
import torch
import torch.nn as nn
@_experiment_module
class ExperimentModule(nn.Module):
    def __pre_init__(self, *args, **kwargs):
        # 为什么官方 dataclass 没有 pre init 我气死了。
        super().__init__() # torch 的初始化
        
    def __post_init__(self):
        # dataclass生成的init是没有调用super().__init__()的，所以需要手动调用
        # https://docs.python.org/3/library/dataclasses.html#dataclasses.__post_init__
        # 这里调用PyTorch的init，接下来用户写self.xx = xx就能注册参数、子模块之类的。
        # super().__init__() 
        # 为了防止用户自己忘记写 super().__post_init__() ，我们换个名字方便用户记忆。
        self.setup()
    def setup(self):
        # 用户实现，初始化增量神经网络的增量参数v
        raise NotImplementedError("Should be implemented by subclass! ")
    
    def __repr__(self):
        return super().__repr__()
    
    def extra_repr(self) -> str:
        return super().extra_repr()
    
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        original_repr = cls.__repr__
        original_extra_repr = cls.extra_repr
        # dataclass(cls) # 这个3.10以后是in place的， 不保证？
        _experiment_module(cls) # 这个3.10以后是in place的， 不保证？
        dataclass_repr = cls.__repr__
        def extra_repr(self):
            dcr = dataclass_repr(self)
            dcr = dcr[dcr.index("(")+1:dcr.rindex(")")]
            return dcr+original_extra_repr(self)
        # cls.extra_repr = lambda self:(dataclass_repr(self)+original_extra_repr(self)) # dataclass的 repr提供给PyTorch
        cls.extra_repr = extra_repr # dataclass的 repr提供给PyTorch
        cls.__repr__ = original_repr
