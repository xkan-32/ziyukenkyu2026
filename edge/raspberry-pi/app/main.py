"""Raspberry Pi メイン処理 — プレースホルダー."""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    """観測・水やりサイクルのエントリポイント."""
    logger.info("komatsuna-agent 起動")

    # TODO: カメラ撮影
    # capture.capture_image()

    # TODO: Arduino から土壌水分取得
    # serial_client.read_moisture()

    # TODO: GCP へアップロード（GCS / Firestore）
    # storage_upload.upload_image(...)
    # firestore_sync.save_observation(...)

    # TODO: AI 判断取得
    # agent_api_client.request_judge(...)

    # TODO: Arduino へ水やり命令
    # serial_client.send_water_command(duration_sec=5)

    # TODO: 水やり後の効果測定（post_watering_scheduler）
    # post_watering_scheduler.run_effect_measurement(...)

    logger.info("処理完了（プレースホルダー）")


if __name__ == "__main__":
    main()
