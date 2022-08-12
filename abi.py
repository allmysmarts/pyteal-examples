# Computed Values 

from typing import Literal as L
from pyteal import *

@Subroutine(TealType.none)
def assert_sum_equals(
    array: abi.StaticArray[abi.Uint64, L[10]], expected_sum: Expr
) -> Expr:
    """This subroutine asserts that the sum of the elements in `array` equals `expected_sum`"""
    i = ScratchVar(TealType.uint64)
    actual_sum = ScratchVar(TealType.uint64)
    tmp_value = abi.Uint64()
    return Seq(
        For(i.store(Int(0)), i.load() < array.length(), i.store(i.load() + Int(1))).Do(
            If(i.load() <= Int(5))
            # Both branches of this If statement are equivalent
            .Then(
                # This branch showcases how to use `store_into`
                Seq(
                    array[i.load()].store_into(tmp_value),
                    actual_sum.store(actual_sum.load() + tmp_value.get()),
                )
            ).Else(
                # This branch showcases how to use `use`
                array[i.load()].use(
                    lambda value: actual_sum.store(actual_sum.load() + value.get())
                )
            )
        ),
        Assert(actual_sum.load() == expected_sum),
    )