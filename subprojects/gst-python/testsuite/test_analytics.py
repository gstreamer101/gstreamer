# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4
#
# gst-python - Python bindings for GStreamer
# Copyright (C) 2024 Collabora Ltd
#  Author: Olivier Crête <olivier.crete@collabora.com>
# Copyright (C) 2024 Intel Corporation
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA

import overrides_hack
overrides_hack

from common import TestCase
import unittest
import sys

import gi
gi.require_version("GLib", "2.0")
gi.require_version("Gst", "1.0")
gi.require_version("GstAnalytics", "1.0")
gi.require_version("GstVideo", "1.0")
from gi.repository import GLib
from gi.repository import Gst
from gi.repository import GstAnalytics
from gi.repository import GstVideo
Gst.init(None)


class TestAnalyticsODMtd(TestCase):
    def test(self):
        buf = Gst.Buffer()
        self.assertIsNotNone(buf)

        meta = GstAnalytics.buffer_add_analytics_relation_meta(buf)
        self.assertIsNotNone(meta)

        m2 = GstAnalytics.buffer_get_analytics_relation_meta(buf)
        self.assertEqual(meta, m2)

        qk = GLib.quark_from_string("testQuark")

        (ret, mtd) = meta.add_od_mtd(qk, 10, 20, 30, 40, 0.3)
        self.assertTrue(ret)
        self.assertIsNotNone(mtd)

        (ret, mtd) = meta.get_od_mtd(0)
        self.assertTrue(ret)
        self.assertIsNotNone(mtd)

        # Ensure there is no mtd 1, only 0
        (ret, _) = meta.get_mtd(1, GstAnalytics.MTD_TYPE_ANY)
        self.assertFalse(ret)

        # The is only one od mtd
        (ret, _) = meta.get_od_mtd(1)
        self.assertFalse(ret)

        # There is no Class mtd
        (ret, _) = meta.get_cls_mtd(0)
        self.assertFalse(ret)

        # meta and m2 should return the same tuple
        self.assertEqual(meta.get_od_mtd(0)[1].get_location(),
                         m2.get_od_mtd(0)[1].get_location())

        self.assertEqual(mtd.get_obj_type(), qk)

        location = meta.get_od_mtd(0)[1].get_location()
        self.assertEqual(location[1], 10)
        self.assertEqual(location[2], 20)
        self.assertEqual(location[3], 30)
        self.assertEqual(location[4], 40)
        self.assertAlmostEqual(location[5], 0.3, 3)

        location = meta.get_od_mtd(0)[1].get_oriented_location()
        self.assertEqual(location[1], 10)
        self.assertEqual(location[2], 20)
        self.assertEqual(location[3], 30)
        self.assertEqual(location[4], 40)
        self.assertEqual(location[5], 0)
        self.assertAlmostEqual(location[6], 0.3, 3)

        (ret, mtd) = meta.add_oriented_od_mtd(qk, 600, 400, 200, 100, 0.785, 0.3)
        self.assertTrue(ret)
        self.assertIsNotNone(mtd)

        (ret, mtd) = meta.get_od_mtd(1)
        self.assertTrue(ret)
        self.assertIsNotNone(mtd)

        location = mtd.get_oriented_location()
        self.assertEqual(location[1], 600)
        self.assertEqual(location[2], 400)
        self.assertEqual(location[3], 200)
        self.assertEqual(location[4], 100)
        self.assertAlmostEqual(location[5], 0.785, 3)
        self.assertAlmostEqual(location[6], 0.3, 3)

        location = mtd.get_location()
        self.assertEqual(location[1], 594)
        self.assertEqual(location[2], 344)
        self.assertEqual(location[3], 212)
        self.assertEqual(location[4], 212)
        self.assertAlmostEqual(location[5], 0.3, 3)


class TestAnalyticsClsMtd(TestCase):
    def test(self):
        buf = Gst.Buffer()
        self.assertIsNotNone(buf)

        meta = GstAnalytics.buffer_add_analytics_relation_meta(buf)
        self.assertIsNotNone(meta)

        qks = (GLib.quark_from_string("q1"),
              GLib.quark_from_string("q2"),
              GLib.quark_from_string("q3"))

        (ret, mtd) = meta.add_cls_mtd([0.1, 0.2, 0.3], qks)
        self.assertTrue(ret)
        self.assertIsNotNone(mtd)

        cnt = mtd.get_length()
        self.assertEqual(cnt, 3)

        for i in range(cnt):
            self.assertEqual(mtd.get_index_by_quark(qks[i]), i)
            self.assertAlmostEqual(mtd.get_level(i), (i + 1) / 10, 7)
            self.assertEqual(mtd.get_quark(i), qks[i])


class TestAnalyticsTrackingMtd(TestCase):
    def test(self):
        buf = Gst.Buffer()
        self.assertIsNotNone(buf)

        meta = GstAnalytics.buffer_add_analytics_relation_meta(buf)
        self.assertIsNotNone(meta)

        (ret, mtd) = meta.add_tracking_mtd(1, 10)
        self.assertTrue(ret)
        rets = mtd.get_info()
        self.assertFalse(rets.tracking_lost)
        self.assertEqual(rets.tracking_first_seen, 10)
        self.assertEqual(rets.tracking_last_seen, 10)

        mtd.update_last_seen(20)

        rets = mtd.get_info()
        self.assertEqual(rets.tracking_first_seen, 10)
        self.assertEqual(rets.tracking_last_seen, 20)

        mtd.set_lost()
        rets = mtd.get_info()
        self.assertTrue(rets.tracking_lost)


class TestAnalyticsSegmentationMtd(TestCase):
    def test(self):
        buf = Gst.Buffer()
        self.assertIsNotNone(buf)

        meta = GstAnalytics.buffer_add_analytics_relation_meta(buf)
        self.assertIsNotNone(meta)

        mask_buf = Gst.Buffer.new_allocate(None, 100, None)
        GstVideo.buffer_add_video_meta(mask_buf,
                                       GstVideo.VideoFrameFlags.NONE,
                                       GstVideo.VideoFormat.GRAY8, 10, 10)

        (ret, mtd) = meta.add_segmentation_mtd(mask_buf,
                                               GstAnalytics.SegmentationType.SEMANTIC,
                                               [7, 4, 2], 0, 0, 7, 13)
        self.assertTrue(ret)

        self.assertEqual((mask_buf, 0, 0, 7, 13), mtd.get_mask())
        self.assertEqual(mtd.get_region_count(), 3)
        self.assertEqual(mtd.get_region_id(0), 7)
        self.assertEqual(mtd.get_region_id(1), 4)
        self.assertEqual(mtd.get_region_id(2), 2)

        self.assertEqual(mtd.get_region_index(1), (False, 0))
        self.assertEqual(mtd.get_region_index(7), (True, 0))
        self.assertEqual(mtd.get_region_index(4), (True, 1))
        self.assertEqual(mtd.get_region_index(2), (True, 2))


class TestAnalyticsTensorMeta(TestCase):
    def test(self):
        buf = Gst.Buffer()
        self.assertIsNotNone(buf)

        tmeta = GstAnalytics.buffer_add_tensor_meta(buf)
        self.assertIsNotNone(tmeta)

        data = Gst.Buffer.new_allocate(None, 2 * 3 * 4)
        self.assertIsNotNone(data)

        tensor = GstAnalytics.Tensor.new_simple(0, GstAnalytics.TensorDataType.UINT8,
                                                data,
                                                GstAnalytics.TensorDimOrder.ROW_MAJOR,
                                                [1, 2, 3, 4])
        self.assertIsNotNone(tensor)
        self.assertEqual(tensor.id, 0)
        self.assertEqual(tensor.num_dims, 4)
        dims = tensor.get_dims()
        self.assertEqual(len(dims), 4)
        self.assertEqual(dims[0], 1)
        self.assertEqual(dims[1], 2)
        self.assertEqual(dims[2], 3)
        self.assertEqual(dims[3], 4)
        self.assertEqual(tensor.data, data)
        self.assertEqual(tensor.data_type, GstAnalytics.TensorDataType.UINT8)
        self.assertEqual(tensor.dims_order, GstAnalytics.TensorDimOrder.ROW_MAJOR)

        data2 = Gst.Buffer.new_allocate(None, 2 * 3 * 4 * 5)
        tensor2 = GstAnalytics.Tensor.new_simple(0, GstAnalytics.TensorDataType.UINT16,
                                                data2,
                                                GstAnalytics.TensorDimOrder.ROW_MAJOR,
                                                [1, 3, 4, 5])
        tmeta.set([tensor, tensor2])

        tmeta2 = GstAnalytics.buffer_get_tensor_meta(buf)
        self.assertEqual(tmeta2.num_tensors, 2)
        self.assertEqual(tmeta2.get(0).data, data)
        self.assertEqual(tmeta2.get(1).data, data2)

        data3 = Gst.Buffer.new_allocate(None, 30)
        tensor3 = GstAnalytics.Tensor.new_simple(0,
                                                 GstAnalytics.TensorDataType.UINT16,
                                                 data3,
                                                 GstAnalytics.TensorDimOrder.ROW_MAJOR,
                                                 [0, 2, 5])
        self.assertIsNotNone(tensor3)


class TestAnalyticsRelationMetaIterator(TestCase):
    def test(self):
        buf = Gst.Buffer()
        self.assertIsNotNone(buf)

        rmeta = GstAnalytics.buffer_add_analytics_relation_meta(buf)
        self.assertIsNotNone(rmeta)

        mask_buf = Gst.Buffer.new_allocate(None, 100, None)
        GstVideo.buffer_add_video_meta(mask_buf,
                                       GstVideo.VideoFrameFlags.NONE,
                                       GstVideo.VideoFormat.GRAY8, 10, 10)

        (_, od_mtd) = rmeta.add_od_mtd(GLib.quark_from_string("od"), 1, 1, 2, 2, 0.1)
        (_, od_mtd1) = rmeta.add_od_mtd(GLib.quark_from_string("od"), 1, 1, 2, 2, 0.1)
        (_, od_mtd2) = rmeta.add_od_mtd(GLib.quark_from_string("od"), 1, 1, 2, 2, 0.1)
        (_, cls_mtd) = rmeta.add_one_cls_mtd(0.1, GLib.quark_from_string("cls"))
        (_, cls_mtd1) = rmeta.add_one_cls_mtd(0.4, GLib.quark_from_string("cls"))
        (_, trk_mtd) = rmeta.add_tracking_mtd(1, 10)
        (_, trk_mtd1) = rmeta.add_tracking_mtd(1, 11)
        (_, seg_mtd) = rmeta.add_segmentation_mtd(mask_buf,
                                               GstAnalytics.SegmentationType.SEMANTIC,
                                               [7, 4, 2], 0, 0, 7, 13)

        mtds = [
            (od_mtd, GstAnalytics.ODMtd.get_mtd_type()),
            (od_mtd1, GstAnalytics.ODMtd.get_mtd_type()),
            (od_mtd2, GstAnalytics.ODMtd.get_mtd_type()),
            (cls_mtd, GstAnalytics.ClsMtd.get_mtd_type()),
            (cls_mtd1, GstAnalytics.ClsMtd.get_mtd_type()),
            (trk_mtd, GstAnalytics.TrackingMtd.get_mtd_type()),
            (trk_mtd1, GstAnalytics.TrackingMtd.get_mtd_type()),
            (seg_mtd, GstAnalytics.SegmentationMtd.get_mtd_type())
        ]

        od_index_mtds = [0, 1, 2]
        cls_index_mtds = [3, 4]
        trk_index_mtds = [5, 6]
        seg_index_mtds = [7]

        mtds_from_iter = list(rmeta)

        self.assertEqual(len(mtds), len(mtds_from_iter))

        # Iterating on type GstAnalytics.ODMtd
        for j, i in zip(od_index_mtds, rmeta.iter_on_type(GstAnalytics.ODMtd)):
            assert mtds[j][0] == i
            assert mtds[j][0].id == i.id
            assert mtds[j][0].meta == i.meta
            assert mtds[j][1] == i.get_mtd_type()
            # call a method to ensure it's a ODMtd
            loc = i.get_location()


        # Iterating on type GstAnalytics.ClsMtd
        for j, i in zip(cls_index_mtds, rmeta.iter_on_type(GstAnalytics.ClsMtd)):
            assert mtds[j][0] == i
            assert mtds[j][0].id == i.id
            assert mtds[j][0].meta == i.meta
            assert mtds[j][1] == i.get_mtd_type()
            # call a method to ensure it's a ClsMtd
            level = i.get_level(0)

        # Iterating on type GstAnalytics.TrackingMtd
        for j, i in zip(trk_index_mtds, rmeta.iter_on_type(GstAnalytics.TrackingMtd)):
            assert mtds[j][0] == i
            assert mtds[j][0].id == i.id
            assert mtds[j][0].meta == i.meta
            assert mtds[j][1] == i.get_mtd_type()
            # call a method to ensure it's a TrackingMtd
            info = i.get_info()

        # Iterating on type GstAnalytics.SegmentationMtd
        for j, i in zip(seg_index_mtds, rmeta.iter_on_type(GstAnalytics.SegmentationMtd)):
            assert mtds[j][0] == i
            assert mtds[j][0].id == i.id
            assert mtds[j][0].meta == i.meta
            assert mtds[j][1] == i.get_mtd_type()
            # call a method to ensure it's a SegmentationMtd
            mask = i.get_mask()

        # Iterating on all type
        for e, i in zip(mtds, rmeta):
            assert i == e[0]
            assert e[0].id == i.id
            assert e[0].meta == i.meta
            assert e[1] == i.get_mtd_type()

        # Validate that the object is really a ODMtd
        location = mtds_from_iter[0].get_location()
        self.assertEqual(location[1], 1)
        self.assertEqual(location[2], 1)
        self.assertEqual(location[3], 2)
        self.assertEqual(location[4], 2)
        self.assertAlmostEqual(location[5], 0.1, 3)

        # Test iteration over direct relation
        rmeta.set_relation(GstAnalytics.RelTypes.RELATE_TO, od_mtd.id, od_mtd1.id)
        rmeta.set_relation(GstAnalytics.RelTypes.IS_PART_OF, od_mtd.id, trk_mtd.id)
        rmeta.set_relation(GstAnalytics.RelTypes.RELATE_TO, od_mtd.id, od_mtd2.id)
        rmeta.set_relation(GstAnalytics.RelTypes.RELATE_TO, od_mtd.id, cls_mtd.id)
        expected_mtd_ids = [od_mtd1.id, od_mtd2.id, cls_mtd.id]
        expected_mtd_type = [GstAnalytics.ODMtd, GstAnalytics.ODMtd, GstAnalytics.ClsMtd]
        count = 0
        # Iterate over all type
        for mtd in od_mtd.iter_direct_related(GstAnalytics.RelTypes.RELATE_TO):
            assert mtd.id == expected_mtd_ids[count]
            assert type(mtd) == expected_mtd_type[count]
            if (type(mtd) == GstAnalytics.ODMtd):
                assert mtd.get_obj_type() == GLib.quark_from_string("od")
            elif (type(mtd) == GstAnalytics.ClsMtd):
                assert mtd.get_quark(0) == GLib.quark_from_string("cls")
            count = count + 1

        assert(count == len(expected_mtd_ids))

        # Iterate over only with type GstAnalytics.ODMtd
        count = 0
        for mtd in od_mtd.iter_direct_related(GstAnalytics.RelTypes.RELATE_TO, GstAnalytics.ODMtd):
            assert mtd.id == expected_mtd_ids[count]
            assert  type(mtd) == GstAnalytics.ODMtd
            count = count + 1

        assert(count == 2)

        # Create a relation path as od_mtd -> cls_mtd -> trk_mtd -> seg_mtd
        rmeta.set_relation(GstAnalytics.RelTypes.NONE, od_mtd.id, trk_mtd.id) # clear relation
        rmeta.set_relation(GstAnalytics.RelTypes.RELATE_TO, cls_mtd.id, trk_mtd.id)
        rmeta.set_relation(GstAnalytics.RelTypes.RELATE_TO, trk_mtd.id, seg_mtd.id)
        count = 0
        expected_rel_ids = [od_mtd.id, cls_mtd.id, trk_mtd.id, seg_mtd.id]
        for i in od_mtd.relation_path(seg_mtd, max_span=4):
            assert i == expected_rel_ids[count]
            count += 1
        assert(count == 4)
