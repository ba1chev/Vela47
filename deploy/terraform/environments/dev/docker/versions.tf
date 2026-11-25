terraform {
  required_version = ">= 1.10"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "4.7.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "3.9.1"
    }
  }
}
