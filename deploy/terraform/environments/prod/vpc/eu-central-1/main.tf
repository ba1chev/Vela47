module "vpc" {
  source = "../../../../modules/vpc"

  name                       = var.name
  cidr_block                 = var.cidr_block
  public_subnet_cidr_blocks  = var.public_subnet_cidr_blocks
  private_subnet_cidr_blocks = var.private_subnet_cidr_blocks
  nat_type                   = var.nat_type
}
