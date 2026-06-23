# TODO: モジュール出力を定義

output "project_id" {
  description = "GCP プロジェクト ID"
  value       = var.project_id
}

output "region" {
  description = "GCP リージョン"
  value       = var.region
}
