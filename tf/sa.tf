resource "random_id" "sa_id" {
  byte_length = 4
}

resource "yandex_iam_service_account" "registry_sa" {
  name = "registry-sa-${random_id.sa_id.hex}"
}

resource "yandex_resourcemanager_folder_iam_member" "registry_push" {
  folder_id = var.yc_folder_id
  role      = "container-registry.images.pusher"
  member    = "serviceAccount:${yandex_iam_service_account.registry_sa.id}"
}

resource "yandex_resourcemanager_folder_iam_member" "registry_pull" {
  folder_id = var.yc_folder_id
  role      = "container-registry.images.puller"
  member    = "serviceAccount:${yandex_iam_service_account.registry_sa.id}"
}

# Меняем editor на admin (или добавляем admin), чтобы экшен мог менять права доступа (public: true)
resource "yandex_resourcemanager_folder_iam_member" "serverless_admin" {
  folder_id = var.yc_folder_id
  role      = "serverless-containers.admin"
  member    = "serviceAccount:${yandex_iam_service_account.registry_sa.id}"
}

resource "yandex_iam_service_account_iam_member" "sa_account_user" {
  service_account_id = yandex_iam_service_account.registry_sa.id
  role               = "iam.serviceAccounts.user"
  member             = "serviceAccount:${yandex_iam_service_account.registry_sa.id}"
}

resource "yandex_iam_service_account_key" "registry_key" {
  service_account_id = yandex_iam_service_account.registry_sa.id
  description        = "key for docker push"
}