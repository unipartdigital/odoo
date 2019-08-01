# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from contextlib import contextmanager
import unittest

import psycopg2
import psycopg2.errorcodes

import odoo
from odoo.tests import common

ADMIN_USER_ID = common.ADMIN_USER_ID

@contextmanager
def environment():
    """ Return an environment with a new cursor for the current database; the
        cursor is committed and closed after the context block.
    """
    registry = odoo.registry(common.get_db_name())
    with registry.cursor() as cr:
        yield odoo.api.Environment(cr, ADMIN_USER_ID, {})
        cr.commit()


def drop_sequence(code):
    with environment() as env:
        seq = env['ir.sequence'].search([('code', '=', code)])
        seq.unlink()


class TestIrSequenceStandard(unittest.TestCase):
    """ A few tests for a 'Standard' (i.e. PostgreSQL) sequence. """

    def test_ir_sequence_create(self):
        """ Try to create a sequence object. """
        with environment() as env:
            seq = env['ir.sequence'].create({
                'code': 'test_sequence_type',
                'name': 'Test sequence',
            })
            self.assertTrue(seq)

    def test_ir_sequence_search(self):
        """ Try a search. """
        with environment() as env:
            seqs = env['ir.sequence'].search([])
            self.assertTrue(seqs)

    def test_ir_sequence_draw(self):
        """ Try to draw a number. """
        with environment() as env:
            n = env['ir.sequence'].next_by_code('test_sequence_type')
            self.assertTrue(n)

    def test_ir_sequence_draw_twice(self):
        """ Try to draw a number from two transactions. """
        with environment() as env0:
            with environment() as env1:
                n0 = env0['ir.sequence'].next_by_code('test_sequence_type')
                self.assertTrue(n0)
                n1 = env1['ir.sequence'].next_by_code('test_sequence_type')
                self.assertTrue(n1)

    @classmethod
    def tearDownClass(cls):
        drop_sequence('test_sequence_type')


class TestIrSequenceNoGap(unittest.TestCase):
    """ Copy of the previous tests for a 'No gap' sequence. """

    def test_ir_sequence_create_no_gap(self):
        """ Try to create a sequence object. """
        with environment() as env:
            seq = env['ir.sequence'].create({
                'code': 'test_sequence_type_2',
                'name': 'Test sequence',
                'implementation': 'no_gap',
            })
            self.assertTrue(seq)

    def test_ir_sequence_draw_no_gap(self):
        """ Try to draw a number. """
        with environment() as env:
            n = env['ir.sequence'].next_by_code('test_sequence_type_2')
            self.assertTrue(n)

    def test_ir_sequence_draw_twice_no_gap(self):
        """ Try to draw a number from two transactions.
        This is expected to not work.
        """
        with environment() as env0:
            with environment() as env1:
                env1.cr._default_log_exceptions = False # Prevent logging a traceback
                with self.assertRaises(psycopg2.OperationalError) as e:
                    n0 = env0['ir.sequence'].next_by_code('test_sequence_type_2')
                    self.assertTrue(n0)
                    n1 = env1['ir.sequence'].next_by_code('test_sequence_type_2')
                self.assertEqual(e.exception.pgcode, psycopg2.errorcodes.LOCK_NOT_AVAILABLE, msg="postgresql returned an incorrect errcode")

    @classmethod
    def tearDownClass(cls):
        drop_sequence('test_sequence_type_2')


class TestIrSequenceChangeImplementation(unittest.TestCase):
    """ Create sequence objects and change their ``implementation`` field. """

    def test_ir_sequence_1_create(self):
        """ Try to create a sequence object. """
        with environment() as env:
            seq = env['ir.sequence'].create({
                'code': 'test_sequence_type_3',
                'name': 'Test sequence',
            })
            self.assertTrue(seq)
            seq = env['ir.sequence'].create({
                'code': 'test_sequence_type_4',
                'name': 'Test sequence',
                'implementation': 'no_gap',
            })
            self.assertTrue(seq)

    def test_ir_sequence_2_write(self):
        with environment() as env:
            domain = [('code', 'in', ['test_sequence_type_3', 'test_sequence_type_4'])]
            seqs = env['ir.sequence'].search(domain)
            seqs.write({'implementation': 'standard'})
            seqs.write({'implementation': 'no_gap'})

    def test_ir_sequence_3_unlink(self):
        with environment() as env:
            domain = [('code', 'in', ['test_sequence_type_3', 'test_sequence_type_4'])]
            seqs = env['ir.sequence'].search(domain)
            seqs.unlink()

    @classmethod
    def tearDownClass(cls):
        drop_sequence('test_sequence_type_3')
        drop_sequence('test_sequence_type_4')


class TestIrSequenceGenerate(unittest.TestCase):
    """ Create sequence objects and generate some values. """

    def test_ir_sequence_create(self):
        """ Try to create a sequence object. """
        with environment() as env:
            seq = env['ir.sequence'].create({
                'code': 'test_sequence_type_5',
                'name': 'Test sequence',
            })
            self.assertTrue(seq)

        with environment() as env:
            for i in range(1, 10):
                n = env['ir.sequence'].next_by_code('test_sequence_type_5')
                self.assertEqual(n, str(i))

    def test_ir_sequence_create_no_gap(self):
        """ Try to create a sequence object. """
        with environment() as env:
            seq = env['ir.sequence'].create({
                'code': 'test_sequence_type_6',
                'name': 'Test sequence',
                'implementation': 'no_gap',
            })
            self.assertTrue(seq)

        with environment() as env:
            for i in range(1, 10):
                n = env['ir.sequence'].next_by_code('test_sequence_type_6')
                self.assertEqual(n, str(i))

    @classmethod
    def tearDownClass(cls):
        drop_sequence('test_sequence_type_5')
        drop_sequence('test_sequence_type_6')


class TestIrSequenceInit(common.TransactionCase):

    def test_00(self):
        """ test whether the read method returns the right number_next value
            (from postgreSQL sequence and not ir_sequence value)
        """
        # first creation of sequence (normal)
        seq = self.env['ir.sequence'].create({
            'number_next': 1,
            'company_id': 1,
            'padding': 4,
            'number_increment': 1,
            'implementation': 'standard',
            'name': 'test-sequence-00',
        })
        # Call next() 4 times, and check the last returned value
        seq.next_by_id()
        seq.next_by_id()
        seq.next_by_id()
        n = seq.next_by_id()
        self.assertEqual(n, "0004", 'The actual sequence value must be 4. reading : %s' % n)
        # reset sequence to 1 by write()
        seq.write({'number_next': 1})
        # Read the value of the current sequence
        n = seq.next_by_id()
        self.assertEqual(n, "0001", 'The actual sequence value must be 1. reading : %s' % n)


class TestIrSequenceCacheClearing(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.company_id = 1

        self.IrSequence = self.env['ir.sequence']

        # Testing invalidates caches randomly, so clear them before doing anything. In particular this means
        # that calling reset_changes again does nothing unless the cache is invalidated by something we do.
        self.IrSequence.pool.reset_changes()

        self.seq = self.IrSequence.create({
            'company_id': self.company_id,
            'name': 'Test Sequence',
            'code': 'test.sequence',
        })

    def test_create_ir_sequence_clears_cache(self):
        """Check that creating a sequence then rolling back the transaction does not result in stale
        cache entries, as long as the registry is reset."""
        try:
            with self.cr.savepoint():
                self.IrSequence.create({
                    'company_id': self.company_id,
                    'name': 'Test Sequence 2',
                    'code': 'test.sequence.2',
                })
                _ = self.IrSequence.seq_by_code('test.sequence.2', self.company_id)
                raise Exception()
        except Exception:
            pass
        # When the sequence was created, caches were cleared, but they have not been cleared since the call to
        # seq_by_code. However in "normal circumstances", a rollback will be triggered by an exception which will cause
        # the following to happen.
        self.IrSequence.pool.reset_changes()
        id = self.IrSequence.seq_by_code('test.sequence.2', self.company_id)
        self.assertEqual(id, False, 'seq_by_code returned an id when the id is invalid due to a '
                                    'rollback since creation')

    def test_delete_ir_sequence_clears_cache(self):
        """Check that deleting a sequence removes stale cache entries"""
        _ = self.IrSequence.seq_by_code('test.sequence', self.company_id)
        self.seq.unlink()
        id = self.IrSequence.seq_by_code('test.sequence', self.company_id)
        self.assertEqual(id, False, 'seq_by_code returned an id when the record has been deleted')

    def test_write_ir_sequence_clears_cache(self):
        """Check that altering a sequence removes stale cache entries."""
        _ = self.IrSequence.seq_by_code('test.sequence', self.company_id)
        self.seq.write({'code': 'test.sequence.changed'})
        id = self.IrSequence.seq_by_code('test.sequence', self.company_id)
        self.assertEqual(id, False, "seq_by_code returned an id for a code which doesn't exist")
