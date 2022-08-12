# Setting values

from pyteal import *

my_address = abi.make(abi.Address)
my_bool = abi.make(abi.Bool)
my_uint64 = abi.make(abi.Uint64)
my_tuple = abi.make(abi.Tuple3[abi.Address, abi.Bool, abi.Uint64])

program = Seq(
    my_address.set(Txn.sender()),
    my_bool.set(Txn.fee() == Int(0)),
    # It's ok to set an abi.Uint to a Python integer. This is actually preferred since PyTeal
    # can determine at compile-time that the value will fit in the integer type.
    my_uint64.set(5000),
    my_tuple.set(my_address, my_bool, my_uint64)
)


# Getting single values

from pyteal import *

@Subroutine(TealType.uint64)
def minimum(a: abi.Uint64, b: abi.Uint64) -> Expr:
    """Return the minimum value of the two arguments."""
    return (
        If(a.get() < b.get())
        .Then(a.get())
        .Else(b.get())
    )


# Getting values at indexes

from typing import Literal as L
from pyteal import *

@Subroutine(TealType.none)
def ensure_all_values_greater_than_5(array: abi.StaticArray[abi.Uint64, L[10]]) -> Expr:
    """This subroutine asserts that every value in the input array is greater than 5."""
    i = ScratchVar(TealType.uint64)
    return For(
        i.store(Int(0)), i.load() < array.length(), i.store(i.load() + Int(1))
    ).Do(
        array[i.load()].use(lambda value: Assert(value.get() > Int(5)))
    )

# Getting referenced value

from pyteal import *

@Subroutine(TealType.none)
def send_inner_txns(
    receiver: abi.Account, asset_to_transfer: abi.Asset, app_to_call: abi.Application
) -> Expr:
    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.receiver: receiver.address(),
                TxnField.xfer_asset: asset_to_transfer.asset_id(),
                TxnField.amount: Int(1_000_000),
            }
        ),
        InnerTxnBuilder.Submit(),
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.ApplicationCall,
                TxnField.application_id: app_to_call.application_id(),
                Txn.application_args: [Bytes("hello")],
            }
        ),
        InnerTxnBuilder.Submit(),
    )


# Accessing parameters of referenced value

from pyteal import *

@Subroutine(TealType.none)
def referenced_params_example(
    account: abi.Account, asset: abi.Asset, app: abi.Application
) -> Expr:
    return Seq(
        account.params().auth_address().outputReducer(
            lambda value, has_value: Assert(And(has_value, value == Global.zero_address()))
        ),
        asset.params().total().outputReducer(
            lambda value, has_value: Assert(And(has_value, value == Int(1)))
        ),
        app.params().creator_address().outputReducer(
            lambda value, has_value: Assert(And(has_value, value == Txn.sender()))
        )
    )