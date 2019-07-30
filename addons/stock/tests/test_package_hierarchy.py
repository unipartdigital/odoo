"""Test package hierarchy."""

from odoo.exceptions import ValidationError
from odoo.tests import common


class TestPackageInheritance(common.TransactionCase):
    """Tests for inheritance and recursion."""

    def setUp(self):
        """Set up three packages."""
        super(TestPackageInheritance, self).setUp()

        Package = self.env["stock.quant.package"]

        # Create 3 empty packages.
        self.package_1 = Package.create({})
        self.package_2 = Package.create({})
        self.package_3 = Package.create({})

    def test_self_cannot_be_parent(self):
        """Test that a package cannot be set as its own parent."""
        with self.assertRaises(ValidationError):
            self.package_1.write({"parent_id": self.package_1.id})

    def test_child_cannot_be_parent(self):
        """Test that a package's child cannot be set as its parent."""
        self.package_2.write({"parent_id": self.package_1.id})
        with self.assertRaises(ValidationError):
            self.package_1.write({"parent_id": self.package_2.id})

    def test_gradchild_cannot_be_parent(self):
        """Test that a package's child's child cannot be set as its parent."""
        self.package_2.write({"parent_id": self.package_1.id})
        self.package_3.write({"parent_id": self.package_2.id})
        with self.assertRaises(ValidationError):
            self.package_1.write({"parent_id": self.package_3.id})

    def test_self_cannot_be_child(self):
        """Test that a package cannot be set as its own child."""
        with self.assertRaises(ValidationError):
            self.package_1.write({"children_ids": [(4, self.package_1.id, False)]})

    def test_parent_cannot_be_child(self):
        """Test that a package's parent cannot be set as its child."""
        self.package_1.write({"parent_id": self.package_2.id})
        with self.assertRaises(ValidationError):
            self.package_1.write({"children_ids": [(4, self.package_2.id, False)]})

    def test_grandparent_cannot_be_child(self):
        """Test that a package's parent's parent cannot be set as its child."""
        self.package_1.write({"parent_id": self.package_2.id})
        self.package_2.write({"parent_id": self.package_3.id})
        with self.assertRaises(ValidationError):
            self.package_1.write({"children_ids": [(4, self.package_3.id, False)]})
