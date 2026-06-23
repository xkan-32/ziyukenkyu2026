# dev 環境 — GCP リソース定義
# TODO: モジュール呼び出しを実装する

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # TODO: GCS バックエンドを設定
  # backend "gcs" {
  #   bucket = "komatsuna-ai-agent-tfstate"
  #   prefix = "dev"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# TODO: storage モジュール
# TODO: firestore モジュール
# TODO: service_accounts モジュール
# TODO: secret_manager モジュール
# TODO: cloud_run モジュール
# TODO: scheduler モジュール
# TODO: line_webhook モジュール（将来）
