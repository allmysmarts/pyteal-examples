from pyteal import *
import json

@Subroutine(TealType.none)
def assert_sender_is_creator() -> Expr:
    return Assert(Txn.sender() == Global.creator_address())

transfer_balance_to_lost = App.globalPut(
    Bytes("lost"),
    App.globalGet(Bytes("lost")) + App.localGet(Txn.sender(), Bytes("balance")),
)

router = Router(
    name="AlgoBank",
    bare_calls=BareCallActions(
        no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE),
        opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL),
        close_out=OnCompleteAction(
            action=transfer_balance_to_lost, call_config=CallConfig.CALL
        ),
        clear_state=OnCompleteAction(
            action=transfer_balance_to_lost, call_config=CallConfig.CALL
        ),
        update_application=OnCompleteAction(
            action=assert_sender_is_creator, call_config=CallConfig.CALL
        ),
        delete_application=OnCompleteAction(
            action=assert_sender_is_creator, call_config=CallConfig.CALL
        ),
    ),
)

@router.method(no_op=CallConfig.CALL, opt_in=CallConfig.CALL)
def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:
    return Seq(
        Assert(payment.get().sender() == sender.address()),
        Assert(payment.get().receiver() == Global.current_application_address()),
        App.localPut(
            sender.address(),
            Bytes("balance"),
            App.localGet(sender.address(), Bytes("balance")) + payment.get().amount(),
        ),
    )

@router.method
def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:
    return output.set(
        App.localGet(user.address(), Bytes("balance"))
    )

@router.method
def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:
    return Seq(
        App.localPut(
            Txn.sender(),
            Bytes("balance"),
            App.localGet(Txn.sender(), Bytes("balance")) - amount.get(),
        ),
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.Payment,
                TxnField.receiver: recipient.address(),
                TxnField.amount: amount.get(),
                TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Submit(),
    )

approval_program, clear_state_program, contract = router.compile_program(
    version=6, optimize=OptimizeOptions(scratch_slots=True)
)

if __name__ == "__main__":
    with open("./abi/algobank_approval.teal", "w") as f:
        f.write(approval_program)

    with open("./abi/algobank_clear_state.teal", "w") as f:
        f.write(clear_state_program)

    with open("./abi/algobank.json", "w") as f:
        f.write(json.dumps(contract.dictify(), indent=4))

