from src.watermark_service import WorkOrder, client_from_environment, prepare_external_share


def main() -> None:
    order = WorkOrder("WO-1042", "data:application/pdf;base64,JVBERi0xLjQK", "dispatched", "Replaced valve")
    decision = prepare_external_share(order, client_from_environment())
    print(decision)


if __name__ == "__main__":
    main()
