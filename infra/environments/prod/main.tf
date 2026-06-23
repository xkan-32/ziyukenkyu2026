# prod 環境 — GCP リソース定義
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
  #   prefix = "prod"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# TODO: dev と同様のモジュール構成（本番用パラメータ）
