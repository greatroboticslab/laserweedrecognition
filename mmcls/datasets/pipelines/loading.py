# Copyright (c) OpenMMLab. All rights reserved.
import os.path as osp

import mmcv
import numpy as np

from ..builder import PIPELINES


@PIPELINES.register_module()
class LoadImageFromFile(object):
    """Load an image from file.

    Required keys are "img_prefix" and "img_info" (a dict that must contain the
    key "filename"). Added or updated keys are "filename", "img", "img_shape",
    "ori_shape" (same as `img_shape`) and "img_norm_cfg" (means=0 and stds=1).

    Args:
        to_float32 (bool): Whether to convert the loaded image to a float32
            numpy array. If set to False, the loaded image is an uint8 array.
            Defaults to False.
        color_type (str): The flag argument for :func:`mmcv.imfrombytes()`.
            Defaults to 'color'.
        file_client_args (dict): Arguments to instantiate a FileClient.
            See :class:`mmcv.fileio.FileClient` for details.
            Defaults to ``dict(backend='disk')``.
    """

    def __init__(self,
                 to_float32=False,
                 color_type='color',
                 file_client_args=dict(backend='disk')):
        self.to_float32 = to_float32
        self.color_type = color_type
        self.file_client_args = file_client_args.copy()
        self.file_client = None

    def __call__(self, results):
        if self.file_client is None:
            self.file_client = mmcv.FileClient(**self.file_client_args)

        if results['img_prefix'] is not None:
            filename = osp.join(results['img_prefix'],
                                results['img_info']['filename'])
        else:
            filename = results['img_info']['filename']

        img_bytes = self.file_client.get(filename)
        img = mmcv.imfrombytes(img_bytes, flag=self.color_type)
        if self.to_float32:
            img = img.astype(np.float32)

        results['filename'] = filename
        results['ori_filename'] = results['img_info']['filename']
        results['img'] = img
        results['img_shape'] = img.shape
        results['ori_shape'] = img.shape
        num_channels = 1 if len(img.shape) < 3 else img.shape[2]
        results['img_norm_cfg'] = dict(
            mean=np.zeros(num_channels, dtype=np.float32),
            std=np.ones(num_channels, dtype=np.float32),
            to_rgb=False)
        return results

    def __repr__(self):
        repr_str = (f'{self.__class__.__name__}('
                    f'to_float32={self.to_float32}, '
                    f"color_type='{self.color_type}', "
                    f'file_client_args={self.file_client_args})')
        return repr_str


def adjust_size(y_size, cbcr_size):
    if np.mod(y_size, 2) == 1:
        y_size -= 1
        cbcr_size = y_size // 2
    return y_size, cbcr_size

@PIPELINES.register_module()
class DCTFlatten2D(object):
    def __init__(self, mux=0b111):
        self.mux = mux
    def __call__(self, results):
        for key in results.get('img_fields', ['img']):
            img = results[key]
            y, cb, cr = img[0], img[1], img[2]

            if self.mux & 0b100:
                y = F.dct_flatten_2d(y)
            if self.mux & 0b010:
                cb = F.dct_flatten_2d(cb)
            if self.mux & 0b001:
                cr = F.dct_flatten_2d(cr)
            results[key] = y, cb, cr
        return results

class DCTUnflatten3D(object):
    def __init__(self, mux=0b111):
        self.mux = mux

    def __call__(self, results):
        for key in results.get('img_fields', ['img']):
            img = results[key]
            y, cb, cr = img[0], img[1], img[2]

            if self.mux & 0b100:
                y = F.dct_unflatten_3d(y)
            if self.mux & 0b010:
                cb = F.dct_unflatten_3d(cb)
            if self.mux & 0b001:
                cr = F.dct_unflatten_3d(cr)
            results[key] = y, cb, cr
        return results

class ToYCrCb(object):
    def __call__(self, results):
        for key in results.get('img_fields', ['img']):
            img = results[key]
            results[key] = F.to_ycrcb(img)
        return results

class ChromaSubsample(object):
    def __call__(self, results):
        for key in results.get('img_fields', ['img']):
            img = results[key]
            results[key] = F.chroma_subsample(img)
        return results

class ResizedTransformDCT(object):
    def __init__(self):
        self.jpeg_encoder = TurboJPEG(libjpeg_path)
        # self.jpeg_encoder = TurboJPEG('/home/kai.x/work/local/lib/libturbojpeg.so')

    def __call__(self, results):
        for key in results.get('img_fields', ['img']):
            img = results[key]
            img_2x = F.upscale(img, upscale_factor=2)
            dct_y, _, _ = F.transform_dct(img_2x, self.jpeg_encoder)
            img_4x = F.upscale(img_2x, upscale_factor=2)
            _, dct_cb, dct_cr = F.transform_dct(img_4x, self.jpeg_encoder)
            results[key] = [dct_y, dct_cb, dct_cr]
        return results

class TransformUpscaledDCT(object):
    def __init__(self):
        self.jpeg_encoder = TurboJPEG(libjpeg_path)
        # self.jpeg_encoder = TurboJPEG('/home/kai.x/work/local/lib/libturbojpeg.so')

    def __call__(self, img):
        y, cbcr = img[0], img[1]
        dct_y, _, _ = F.transform_dct(y, self.jpeg_encoder)
        _, dct_cb, dct_cr = F.transform_dct(cbcr, self.jpeg_encoder)
        return dct_y, dct_cb, dct_cr

class AdjustDCT(object):
    def __init__(self):
        self.jpeg_encoder = TurboJPEG(libjpeg_path)
        # self.jpeg_encoder = TurboJPEG('/home/kai.x/work/local/lib/libturbojpeg.so')

    def __call__(self, img):
        dct_y, dct_cb, dct_cr = img[0], img[1], img[2]

        y_size_h, y_size_w = dct_y.shape[:-1]
        cbcr_size_h, cbcr_size_w = dct_cb.shape[:-1]
        y_size_h, cbcr_size_h = adjust_size(y_size_h, cbcr_size_h)
        y_size_w, cbcr_size_w = adjust_size(y_size_w, cbcr_size_w)
        dct_y = dct_y[:y_size_h, :y_size_w]
        dct_cb = dct_cb[:cbcr_size_h, :cbcr_size_w]
        dct_cr = dct_cr[:cbcr_size_h, :cbcr_size_w]

        return dct_y, dct_cb, dct_cr

class TransformDCT(object):
    def __init__(self):
        self.jpeg_encoder = TurboJPEG(libjpeg_path)
        # self.jpeg_encoder = TurboJPEG('/home/kai.x/work/local/lib/libturbojpeg.so')

    def __call__(self, img):
        return F.transform_dct(img, self.jpeg_encoder)

class UpsampleDCTOld(object):
    def __init__(self, size=None, upscale_ratio_h=None, upscale_ratio_w=None, L=1, M=1, N=8, T=None,
                 A1=None, A2=None, B1=None, B2=None, debug=False):
        self.L, self.M = L, M
        self.T = T
        self.N = N
        self.A1, self.A2, self.B1, self.B2 = A1, A2, B1, B2
        self.debug = debug

        if size is not None:
            pad_h = 0 if size % (L*N) == 0 else L*N - (size % (L*N))
            pad_w = 0 if size % (M*N) == 0 else M*N - (size % (M*N))
            H = size + pad_h
            W = size + pad_w
            P = L * T // H
            Q = M * T // W
            self.A1 = block_composition(L, N)
            self.A2 = block_composition(M, N)
            self.B1_Y = block_composition(P, N)
            self.B2_Y = block_composition(Q, N)
            self.B1_CbCr = block_composition(P*2, N)
            self.B2_CbCr = block_composition(Q*2, N)
        elif upscale_ratio_h is not None and upscale_ratio_w is not None:
            P, Q = upscale_ratio_h, upscale_ratio_w
            self.A1 = block_composition(L, N)
            self.A2 = block_composition(M, N)
            self.B1_Y = block_composition(P, N)
            self.B2_Y = block_composition(Q, N)
            self.B1_CbCr = block_composition(P * 2, N)
            self.B2_CbCr = block_composition(Q * 2, N)
        else:
            raise ValueError
        self.P, self.Q = P, Q

    def __call__(self, img):
        # end = time.time()
        y, cb, cr = img[0], img[1], img[2]

        if not self.debug:
            y, P, Q  = resize_dct(y,  self.L, self.M, A1=self.A1, A2=self.A2, B1=self.B1_Y, B2=self.B2_Y,
                                  P=self.P, Q=self.Q, debug=self.debug)
            cb, _, _ = resize_dct(cb, self.L, self.M, A1=self.A1, A2=self.A2, B1=self.B1_CbCr, B2=self.B2_CbCr,
                                  P=2*self.P, Q=2*self.Q, debug=self.debug)
            cr, _, _ = resize_dct(cr, self.L, self.M, A1=self.A1, A2=self.A2, B1=self.B1_CbCr, B2=self.B2_CbCr,
                                  P=2*self.P, Q=2*self.Q, debug=self.debug)
        else:
            dct_reform_show = minmax_scale(y)
            plt.imshow(dct_reform_show, cmap='gray', vmax=np.max(dct_reform_show), vmin=0)
            plt.show()

            y, rgb_y, y_raw  = resize_dct(y,  self.L, self.M, self.T, A1=self.A1, A2=self.A2, B1=self.B1_Y,
                                          B2=self.B2_Y, P=self.P, Q=self.Q, debug=self.debug)

            dct_reform_show = minmax_scale(y[:, :, 0])
            plt.imshow(dct_reform_show, cmap='gray', vmax=np.max(dct_reform_show), vmin=0)
            plt.show()

            dct_reform_show = minmax_scale(rgb_y)
            plt.imshow(dct_reform_show, cmap='gray', vmax=np.max(dct_reform_show), vmin=0)
            plt.show()

            dct_reform_show = minmax_scale(y_raw)
            plt.imshow(dct_reform_show, cmap='gray', vmax=np.max(dct_reform_show), vmin=0)
            plt.show()

            cb, rgb_cb, cb_raw = resize_dct(cb, self.L, self.M, self.T, A1=self.A1, A2=self.A2, B1=self.B1_CbCr,
                                            B2=self.B2_CbCr, P=2*self.P, Q=2*self.Q, debug=self.debug)
            cr, rgb_cr, cr_raw = resize_dct(cr, self.L, self.M, self.T, A1=self.A1, A2=self.A2, B1=self.B1_CbCr,
                                            B2=self.B2_CbCr, P=2*self.P, Q=2*self.Q, debug=self.debug)

        # print('upsample: {}'.format(time.time()-end))
        return y, cb, cr

class UpsampleDCT(object):
    def __init__(self, L=1, M=1, N=8, T=None, debug=False):
        self.L, self.M = L, M
        self.T = T
        self.N = N
        self.debug = debug

        self.A1 = block_composition(L, N)
        self.A2 = block_composition(M, N)

    def __call__(self, img):
        y, cb, cr = img[0], img[1], img[2]

        P = Q = 1

        y_h, y_w, _ = y.shape
        cbcr_h, cbcr_w, _ = cb.shape

        if not self.debug:
            y, P, Q = resize_dct(y, self.L, self.M, T=self.T, A1=self.A1, A2=self.A2, debug=self.debug, new=True)
            cbcr_P = 2 * P if y_h == 2 * cbcr_h else P
            cbcr_Q = 2 * Q if y_w == 2 * cbcr_w else Q

            cb, _, _ = resize_dct(cb, self.L, self.M, P=cbcr_P, Q=cbcr_Q, A1=self.A1, A2=self.A2, debug=self.debug, new=True)
            cr, _, _ = resize_dct(cr, self.L, self.M, P=cbcr_P, Q=cbcr_Q, A1=self.A1, A2=self.A2, debug=self.debug, new=True)

            # if y.shape != cb.shape:
            #     print(y_h, y_w)
            #     print(cbcr_h, cbcr_w)
            #     print(y.shape)
            #     print(cb.shape)
            #     print(cbcr_P, cbcr_Q, P, Q)
        else:
            y, rgb_y, y_raw  = resize_dct(y, self.L, self.M, T=self.T, A1=self.A1, A2=self.A2, debug=self.debug, new=True)
            cb, _, _ = resize_dct(cb, self.L, self.M, P=P, Q=Q, A1=self.A1, A2=self.A2, debug=self.debug, new=True)
            cr, _, _ = resize_dct(cr, self.L, self.M, P=P, Q=Q, A1=self.A1, A2=self.A2, debug=self.debug, new=True)

            dct_reform_show = minmax_scale(y[:, :, 0])
            plt.imshow(dct_reform_show, cmap='gray', vmax=np.max(dct_reform_show), vmin=0)
            plt.show()

            dct_reform_show = minmax_scale(rgb_y)
            plt.imshow(dct_reform_show, cmap='gray', vmax=np.max(dct_reform_show), vmin=0)
            plt.show()

            dct_reform_show = minmax_scale(y_raw)
            plt.imshow(dct_reform_show, cmap='gray', vmax=np.max(dct_reform_show), vmin=0)
            plt.show()
        # print('upsample: {}'.format(time.time()-end))
        return y, cb, cr

class UpsampleCbCr(object):
    def __init__(self, upscale_factor=2, interpolation='BILINEAR'):
        self.upscale_factor = upscale_factor
        self.interpolation = interpolation

    def __call__(self, img):
        y, cb, cr = img[0], img[1], img[2]

        dh, dw, _ = y.shape
        # y  = F.upscale(y,  desize_size=(dh, dw), interpolation=self.interpolation)
        cb = F.upscale(cb, desize_size=(dh, dw), interpolation=self.interpolation)
        cr = F.upscale(cr, desize_size=(dh, dw), interpolation=self.interpolation)

        return y, cb, cr

class UpsampleCbCrDCT(object):
    def __init__(self, L=1, M=1, N=8, debug=False):
        self.L, self.M = L, M
        self.N = N
        self.debug = debug

        self.A1 = block_composition(L, N)
        self.A2 = block_composition(M, N)

        self.B1_CbCr_1x = block_composition(1, N)
        self.B1_CbCr_2x = block_composition(2, N)

        self.B2_CbCr_1x = block_composition(1, N)
        self.B2_CbCr_2x = block_composition(2, N)

    def __call__(self, img):
        y, cb, cr = img[0], img[1], img[2]
        y_h, y_w = y.shape[:-1]
        cbcr_h, cbcr_w = cb.shape

        if y_h * self.N == 2 * cbcr_h and y_w * self.N == 2 * cbcr_w:
            cb, _, _ = resize_dct(cb, self.L, self.M, A1=self.A1, A2=self.A2, B1=self.B1_CbCr_2x, B2=self.B2_CbCr_2x,
                                  P=2, Q=2, debug=self.debug, fold=True)
            cr, _, _ = resize_dct(cr, self.L, self.M, A1=self.A1, A2=self.A2, B1=self.B1_CbCr_2x, B2=self.B2_CbCr_2x,
                                  P=2, Q=2, debug=self.debug, fold=True)
        elif y_h * self.N == 2 * cbcr_h and y_w * self.N == cbcr_w:
            cb, _, _ = resize_dct(cb, self.L, self.M, A1=self.A1, A2=self.A2, B1=self.B1_CbCr_2x, B2=self.B2_CbCr_1x,
                                  P=2, Q=1, debug=self.debug, fold=True)
            cr, _, _ = resize_dct(cr, self.L, self.M, A1=self.A1, A2=self.A2, B1=self.B1_CbCr_2x, B2=self.B2_CbCr_1x,
                                  P=2, Q=1, debug=self.debug, fold=True)
        elif y_h * self.N == cbcr_h and y_w * self.N == 2 * cbcr_w:
            cb, _, _ = resize_dct(cb, self.L, self.M, A1=self.A1, A2=self.A2, B1=self.B1_CbCr_1x, B2=self.B2_CbCr_2x,
                                  P=1, Q=2, debug=self.debug, fold=True)
            cr, _, _ = resize_dct(cr, self.L, self.M, A1=self.A1, A2=self.A2, B1=self.B1_CbCr_1x, B2=self.B2_CbCr_2x,
                                  P=1, Q=2, debug=self.debug, fold=True)
        elif y_h * self.N == cbcr_h and y_w * self.N == cbcr_w:
            cb = F.dct_unflatten_3d(cb)
            cr = F.dct_unflatten_3d(cr)
        else:
            print('Resolution does not match.')

        return y, cb, cr

# class UpsampleDCTSingleChannel(object):
#     def __init__(self, size_threshold=None, upscale_ratio_h=None, upscale_ratio_w=None, L=1, M=1, N=8, T=None,
#                  A1=None, A2=None, B1=None, B2=None, debug=False):
#         self.L, self.M = L, M
#         self.T = T
#         self.N = N
#         self.A1, self.A2, self.B1, self.B2 = A1, A2, B1, B2
#         self.debug = debug
#         self.size_threshold = size_threshold
#
#     def __call__(self, img):
#         y, cb, cr = img[0], img[1], img[2]
#
#         P = Q = 1
#         y_h, y_w = y.shape
#         if y_h < self.size_threshold:
#             pad_h = 0 if y_h % (self.L * self.N) == 0 else self.L * self.N - (y_h % (self.L * self.N))
#             H = y_h + pad_h
#             P = self.L * self.T // H
#         if y_w < self.size_threshold:
#             pad_w = 0 if y_w % (self.M * self.N) == 0 else self.M * self.N - (y_w % (self.M * self.N))
#             W = y_w + pad_w
#             Q = self.M * self.T // W
#
#         self.A1 = block_composition(self.L, self.N)
#         self.A2 = block_composition(self.M, self.N)
#         self.B1_Y = block_composition(P, self.N)
#         self.B2_Y = block_composition(Q, self.N)
#
#         y, P, Q  = resize_dct(y,  self.L, self.M, A1=self.A1, A2=self.A2, B1=self.B1_Y, B2=self.B2_Y,
#                               P=P, Q=Q, cuda=False, debug=self.debug)
#
#         return y, cb, cr

class DCTCenterCrop(object):
    def __init__(self, size):
        self.size = size

    def __call__(self, img):
        y, cb, cr = img[0], img[1], img[2]
        y = F.center_crop(y, self.size)
        cb = F.center_crop(cb, self.size)
        cr = F.center_crop(cr, self.size)

        return y, cb, cr

class Average(object):
    def __call__(self, img):
        if isinstance(img, list):
            y, cb, cr = img[0], img[1], img[2]
            y = y.view(y.size(0), -1).mean(dim=1)
            cb = cb.view(cb.size(0), -1).mean(dim=1)
            cr = cr.view(cr.size(0), -1).mean(dim=1)
            return y, cb, cr
        else:
            return img.view(img.size(0), -1).mean(dim=1), None, None

class AverageYUV(object):
    def __call__(self, img):
        return img.view(img.size(0), -1).mean(dim=1)

class CenterCropDCT(object):
    """Crops the given PIL Image at the center.

    Args:
        size (sequence or int): Desired output size of the crop. If size is an
            int instead of sequence like (h, w), a square crop (size, size) is
            made.
    """

    def __init__(self, size):
        if isinstance(size, numbers.Number):
            self.size = (int(size), int(size))
        else:
            self.size = size

    def __call__(self, img):
        """
        Args:
            img (PIL Image): Image to be cropped.

        Returns:
            PIL Image: Cropped image.
        """
        end = time.time()
        y, cb, cr = img[0], img[1], img[2]
        y  = F.center_crop(y, self.size)
        cb = F.center_crop(cb, self.size)
        cr = F.center_crop(cr, self.size)
        print('crop: {}'.format(time.time()-end))

        return y, cb, cr


class ToTensorDCT(object):
    """Convert a ``numpy.ndarray`` to tensor.

    Converts a numpy.ndarray (H x W x C) in the range
    [0, 255] to a torch.FloatTensor of shape (C x H x W) in the range [0.0, 1.0].
    """

    def __call__(self, img):
        """
        Args:
            pic (numpy.ndarray): Image to be converted to tensor.

        Returns:
            Tensor: Converted image.
        """
        y, cb, cr = img[0], img[1], img[2]
        y, cb, cr = F.to_tensor_dct(y), F.to_tensor_dct(cb), F.to_tensor_dct(cr)

        return y, cb, cr

class ToTensorDCT2(object):
    """Convert a ``numpy.ndarray`` to tensor.

    Converts a numpy.ndarray (H x W x C) in the range
    [0, 255] to a torch.FloatTensor of shape (C x H x W) in the range [0.0, 1.0].
    """

    def __call__(self, img):
        """
        Args:
            pic (numpy.ndarray): Image to be converted to tensor.

        Returns:
            Tensor: Converted image.
        """
        return F.to_tensor_dct(img)


class Upscale(object):
    def __init__(self, upscale_factor=2, interpolation='BILINEAR'):
        self.upscale_factor = upscale_factor
        self.interpolation = interpolation

    def __call__(self, img):
        return img, F.upscale(img, self.upscale_factor, self.interpolation)


class SubsetDCT(object):
    def __init__(self, channels=20, pattern='square'):
        self.channels = channels

        if pattern == 'square':
            self.subset_channel_index = subset_channel_index_square
        elif pattern == 'learned':
            self.subset_channel_index = subset_channel_index_learned
        elif pattern == 'triangle':
            self.subset_channel_index = subset_channel_index_triangle

        if self.channels < 192:
            self.subset_y =  self.subset_channel_index[channels][0]
            self.subset_cb = self.subset_channel_index[channels][1]
            self.subset_cr = self.subset_channel_index[channels][2]

    def __call__(self, tensor):
        if self.channels < 192:
            dct_y, dct_cb, dct_cr = tensor[0], tensor[1], tensor[2]
            dct_y, dct_cb, dct_cr = dct_y[self.subset_y], dct_cb[self.subset_cb], dct_cr[self.subset_cr]
            return dct_y, dct_cb, dct_cr
        else:
            return tensor[0], tensor[1], tensor[2]

class SubsetDCT2(object):
    def __init__(self, channels=20, pattern='square'):
        if pattern == 'square':
            self.subset_channel_index = subset_channel_index_square
        elif pattern == 'learned':
            self.subset_channel_index = subset_channel_index_learned
        elif pattern == 'triangle':
            self.subset_channel_index = subset_channel_index_triangle

        if channels < 192:
            self.subset_y =  self.subset_channel_index[channels][0]
            self.subset_cb = self.subset_channel_index[channels][1]
            self.subset_cr = self.subset_channel_index[channels][2]

    def __call__(self, tensor):
        dct_y, dct_cb, dct_cr = tensor[0], tensor[1], tensor[2]
        dct_y, dct_cb, dct_cr = dct_y[:,:, self.subset_y], dct_cb[:, :, self.subset_cb], dct_cr[:, :, self.subset_cr]

        return dct_y, dct_cb, dct_cr

class Aggregate(object):
    def __call__(self, img):
        dct_y, dct_cb, dct_cr = img[0], img[1], img[2]
        dct_y = torch.cat((dct_y, dct_cb, dct_cr), dim=0)
        return dct_y

class Aggregate2(object):
    def __call__(self, img):
        dct_y, dct_cb, dct_cr = img[0], img[1], img[2]
        try:
            dct_y = np.concatenate((dct_y, dct_cb, dct_cr), axis=2)
        except:
            print('Y: {}, Cb: {}, Cr: {}'.format(dct_y.shape, dct_cb.shape, dct_cr.shape))
        return dct_y

class NormalizeDCT(object):
    """Normalize a tensor image with mean and standard deviation.
    Given mean: ``(M1,...,Mn)`` and std: ``(S1,..,Sn)`` for ``n`` channels, this transform
    will normalize each channel of the input ``torch.*Tensor`` i.e.
    ``input[channel] = (input[channel] - mean[channel]) / std[channel]``

    Args:
        mean (sequence): Sequence of means for each channel.
        std (sequence): Sequence of standard deviations for each channel.
    """
    def __init__(self, y_mean, y_std, cb_mean=None, cb_std=None, cr_mean=None, cr_std=None, channels=None, pattern='square'):
        self.y_mean,  self.y_std = y_mean, y_std
        self.cb_mean, self.cb_std = cb_mean, cb_std
        self.cr_mean, self.cr_std = cr_mean, cr_std

        if channels < 192:
            if pattern == 'square':
                self.subset_channel_index = subset_channel_index_square
            elif pattern == 'learned':
                self.subset_channel_index = subset_channel_index_learned
            elif pattern == 'triangle':
                self.subset_channel_index = subset_channel_index_triangle

            self.subset_y  = self.subset_channel_index[channels][0]
            self.subset_cb = self.subset_channel_index[channels][1]
            self.subset_cb = [64+c for c in self.subset_cb]
            self.subset_cr = self.subset_channel_index[channels][2]
            self.subset_cr = [128+c for c in self.subset_cr]
            self.subset = self.subset_y + self.subset_cb + self.subset_cr
            self.mean_y, self.std_y = [y_mean[i] for i in self.subset], [y_std[i] for i in self.subset]
        else:
            self.mean_y, self.std_y = y_mean, y_std


    def __call__(self, tensor):
        """
        Args:
            tensor (Tensor): Tensor image of size (C, H, W) to be normalized.

        Returns:
            Tensor: Normalized Tensor image.
        """
        if isinstance(tensor, list):
            y, cb, cr = tensor[0], tensor[1], tensor[2]
            y  = F.normalize(y,  self.y_mean,  self.y_std)
            cb = F.normalize(cb, self.cb_mean, self.cb_std)
            cr = F.normalize(cr, self.cr_mean, self.cr_std)
            return y, cb, cr
        else:
            y = F.normalize(tensor, self.mean_y, self.std_y)
            return y, None, None

class Compose(object):
    """Composes several transforms together.

    Args:
        transforms (list of ``Transform`` objects): list of transforms to compose.

    Example:
        >>> transforms.Compose([
        >>>     transforms.CenterCrop(10),
        >>>     transforms.ToTensor(),
        >>> ])
    """

    def __init__(self, transforms):
        self.transforms = transforms

    def __call__(self, img):
        for t in self.transforms:
            img = t(img)
        return img

    def __repr__(self):
        format_string = self.__class__.__name__ + '('
        for t in self.transforms:
            format_string += '\n'
            format_string += '    {0}'.format(t)
        format_string += '\n)'
        return format_string


class Lambda(object):
    """Apply a user-defined lambda as a transform.
    Attention: The multiprocessing used in dataloader of pytorch is not friendly with lambda function in Windows

    Args:
        lambd (function): Lambda/function to be used for transform.
    """

    def __init__(self, lambd):
        # assert isinstance(lambd, types.LambdaType)
        self.lambd = lambd
        # if 'Windows' in platform.system():
        #     raise RuntimeError("Can't pickle lambda funciton in windows system")

    def __call__(self, img):
        return self.lambd(img)

    def __repr__(self):
        return self.__class__.__name__ + '()'


class ToTensor(object):
    """Convert a ``numpy.ndarray`` to tensor.

    Converts a numpy.ndarray (H x W x C) in the range
    [0, 255] to a torch.FloatTensor of shape (C x H x W) in the range [0.0, 1.0].
    """

    def __call__(self, pic):
        """
        Args:
            pic (numpy.ndarray): Image to be converted to tensor.

        Returns:
            Tensor: Converted image.
        """
        return F.to_tensor(pic)

    def __repr__(self):
        return self.__class__.__name__ + '()'


class ToCVImage(object):
    """Convert a tensor or an to ndarray Image.

    Converts a torch.*Tensor of shape C x H x W or a numpy ndarray of shape
    H x W x C to a CV Image while preserving the value range.

    Args:
        mode (str): color space and pixel depth of input data (optional).
    """
    def __init__(self, mode=None):
        self.mode = mode

    def __call__(self, pic):
        """
        Args:
            pic (Tensor or numpy.ndarray): Image to be converted to PIL Image.

        Returns:
            PIL Image: Image converted to PIL Image.

        """
        return F.to_cv_image(pic, self.mode)


class Normalize(object):
    """Normalize a tensor image with mean and standard deviation.
    Given mean: ``(M1,...,Mn)`` and std: ``(S1,..,Sn)`` for ``n`` channels, this transform
    will normalize each channel of the input ``torch.*Tensor`` i.e.
    ``input[channel] = (input[channel] - mean[channel]) / std[channel]``

    Args:
        mean (sequence): Sequence of means for each channel.
        std (sequence): Sequence of standard deviations for each channel.
    """

    def __init__(self, mean, std):
        self.mean = mean
        self.std = std

    def __call__(self, tensor):
        """
        Args:
            tensor (Tensor): Tensor image of size (C, H, W) to be normalized.

        Returns:
            Tensor: Normalized Tensor image.
        """
        return F.normalize(tensor, self.mean, self.std)

    def __repr__(self):
        return self.__class__.__name__ + '(mean={0}, std={1})'.format(self.mean, self.std)


class Resize(object):
    """Resize the input PIL Image to the given size.

    Args:
        size (sequence or int): Desired output size. If size is a sequence like
            (h, w), output size will be matched to this. If size is an int,
            smaller edge of the image will be matched to this number.
            i.e, if height > width, then image will be rescaled to
            (size * height / width, size)
        interpolation (int, optional): Desired interpolation. Default is
            ``BILINEAR``
    """

    def __init__(self, size, interpolation='BILINEAR'):
        assert isinstance(size, int) or (isinstance(size, collections.Iterable) and len(size) == 2)
        self.size = size
        self.interpolation = interpolation

    def __call__(self, img):
        """
        Args:
            img (np.ndarray): Image to be scaled.

        Returns:
            np.ndarray: Rescaled image.
        """
        return F.resize(img, self.size, self.interpolation)

    def __repr__(self):
        interpolate_str = self.interpolation
        return self.__class__.__name__ + '(size={0}, interpolation={1})'.format(self.size, interpolate_str)


class CenterCrop(object):
    """Crops the given PIL Image at the center.

    Args:
        size (sequence or int): Desired output size of the crop. If size is an
            int instead of sequence like (h, w), a square crop (size, size) is
            made.
    """

    def __init__(self, size):

        self.size = size

    def __call__(self, img):
        """
        Args:
            img (CV Image): Image to be cropped.

        Returns:
            CV Image: Cropped image.
        """
        return F.center_crop(img, self.size)

    def __repr__(self):
        return self.__class__.__name__ + '(size={0})'.format(self.size)


class Pad(object):
    """Pad the given CV Image on all sides with the given "pad" value.

    Args:
        padding (int or tuple): Padding on each border. If a single int is provided this
            is used to pad all borders. If tuple of length 2 is provided this is the padding
            on left/right and top/bottom respectively. If a tuple of length 4 is provided
            this is the padding for the left, top, right and bottom borders
            respectively.
        fill: Pixel fill value for constant fill. Default is 0. If a tuple of
            length 3, it is used to fill R, G, B channels respectively.
            This value is only used when the padding_mode is constant
        padding_mode: Type of padding. Should be: constant, edge, reflect or symmetric. Default is constant.
            constant: pads with a constant value, this value is specified with fill
            edge: pads with the last value at the edge of the image
            reflect: pads with reflection of image (without repeating the last value on the edge)
                padding [1, 2, 3, 4] with 2 elements on both sides in reflect mode
                will result in [3, 2, 1, 2, 3, 4, 3, 2]
            symmetric: pads with reflection of image (repeating the last value on the edge)
                padding [1, 2, 3, 4] with 2 elements on both sides in symmetric mode
                will result in [2, 1, 1, 2, 3, 4, 4, 3]
    """

    def __init__(self, padding, fill=0, padding_mode='constant'):
        assert isinstance(padding, (numbers.Number, tuple))
        assert isinstance(fill, (numbers.Number, str, tuple))
        assert padding_mode in ['constant', 'edge', 'reflect', 'symmetric']
        if isinstance(padding, collections.Sequence) and len(padding) not in [2, 4]:
            raise ValueError("Padding must be an int or a 2, or 4 element tuple, not a " +
                             "{} element tuple".format(len(padding)))

        self.padding = padding
        self.fill = fill
        self.padding_mode = padding_mode

    def __call__(self, img):
        """
        Args:
            img (CV Image): Image to be padded.

        Returns:
            CV Image: Padded image.
        """
        return F.pad(img, self.padding, self.fill, self.padding_mode)

    def __repr__(self):
        return self.__class__.__name__ + '(padding={0}, fill={1}, padding_mode={2})'.\
            format(self.padding, self.fill, self.padding_mode)


class RandomTransforms(object):
    """Base class for a list of transformations with randomness

    Args:
        transforms (list or tuple): list of transformations
    """

    def __init__(self, transforms):
        assert isinstance(transforms, (list, tuple))
        self.transforms = transforms

    def __call__(self, *args, **kwargs):
        raise NotImplementedError()

    def __repr__(self):
        format_string = self.__class__.__name__ + '('
        for t in self.transforms:
            format_string += '\n'
            format_string += '    {0}'.format(t)
        format_string += '\n)'
        return format_string


class RandomApply(RandomTransforms):
    """Apply randomly a list of transformations with a given probability

    Args:
        transforms (list or tuple): list of transformations
        p (float): probability
    """

    def __init__(self, transforms, p=0.5):
        super(RandomApply, self).__init__(transforms)
        self.p = p

    def __call__(self, img):
        if self.p < random.random():
            return img
        for t in self.transforms:
            img = t(img)
        return img

    def __repr__(self):
        format_string = self.__class__.__name__ + '('
        format_string += '\n    p={}'.format(self.p)
        for t in self.transforms:
            format_string += '\n'
            format_string += '    {0}'.format(t)
        format_string += '\n)'
        return format_string


class RandomOrder(RandomTransforms):
    """Apply a list of transformations in a random order
    """
    def __call__(self, img):
        order = list(range(len(self.transforms)))
        random.shuffle(order)
        for i in order:
            img = self.transforms[i](img)
        return img


class RandomChoice(RandomTransforms):
    """Apply single transformation randomly picked from a list
    """
    def __call__(self, img):
        t = random.choice(self.transforms)
        return t(img)


class RandomCrop(object):
    """Crop the given CV Image at a random location.

    Args:
        size (sequence or int): Desired output size of the crop. If size is an
            int instead of sequence like (h, w), a square crop (size, size) is
            made.
        padding (int or sequence, optional): Optional padding on each border
            of the image. Default is 0, i.e no padding. If a sequence of length
            4 is provided, it is used to pad left, top, right, bottom borders
            respectively.
        pad_if_needed (boolean): It will pad the image if smaller than the
            desired size to avoid raising an exception.
    """

    def __init__(self, size, padding=0, pad_if_needed=False):
        if isinstance(size, numbers.Number):
            self.size = (int(size), int(size))
        else:
            self.size = size
        self.padding = padding
        self.pad_if_needed = pad_if_needed

    @staticmethod
    def get_params(img, output_size):
        """Get parameters for ``crop`` for a random crop.

        Args:
            img (CV Image): Image to be cropped.
            output_size (tuple): Expected output size of the crop.

        Returns:
            tuple: params (i, j, h, w) to be passed to ``crop`` for random crop.
        """
        h, w, _ = img.shape
        th, tw = output_size
        if w == tw and h == th:
            return 0, 0, h, w

        try:
            i = random.randint(0, h - th)
        except ValueError:
            i = random.randint(h - th, 0)
        try:
            j = random.randint(0, w - tw)
        except ValueError:
            j = random.randint(w - tw, 0)
        return i, j, th, tw

    def __call__(self, img):
        """
        Args:
            img (np.ndarray): Image to be cropped.

        Returns:
            np.ndarray: Cropped image.
        """
        if self.padding > 0:
            img = F.pad(img, self.padding)

        # pad the width if needed
        if self.pad_if_needed and img.shape[1] < self.size[1]:
            img = F.pad(img, (int((1 + self.size[1] - img.shape[1]) / 2), 0))
        # pad the height if needed
        if self.pad_if_needed and img.shape[0] < self.size[0]:
            img = F.pad(img, (0, int((1 + self.size[0] - img.shape[0]) / 2)))

        i, j, h, w = self.get_params(img, self.size)

        return F.crop(img, i, j, h, w)

    def __repr__(self):
        return self.__class__.__name__ + '(size={0}, padding={1})'.format(self.size, self.padding)


class RandomHorizontalFlip(object):
    """Horizontally flip the given CV Image randomly with a given probability.

    Args:
        p (float): probability of the image being flipped. Default value is 0.5
    """

    def __init__(self, p=0.5):
        self.p = p

    def __call__(self, img):
        """
        Args:
            img (CV Image): Image to be flipped.

        Returns:
            CV Image: Randomly flipped image.
        """
        if random.random() < self.p:
            return F.hflip(img)
        return img

    def __repr__(self):
        return self.__class__.__name__ + '(p={})'.format(self.p)


class RandomVerticalFlip(object):
    """Vertically flip the given CV Image randomly with a given probability.

    Args:
        p (float): probability of the image being flipped. Default value is 0.5
    """

    def __init__(self, p=0.5):
        self.p = p

    def __call__(self, img):
        """
        Args:
            img (CV Image): Image to be flipped.

        Returns:
            CV Image: Randomly flipped image.
        """
        if random.random() < self.p:
            return F.vflip(img)
        return img

    def __repr__(self):
        return self.__class__.__name__ + '(p={})'.format(self.p)


class RandomResizedCrop(object):
    """Crop the given CV Image to random size and aspect ratio.

    A crop of random size (default: of 0.08 to 1.0) of the original size and a random
    aspect ratio (default: of 3/4 to 4/3) of the original aspect ratio is made. This crop
    is finally resized to given size.
    This is popularly used to train the Inception networks.

    Args:
        size: expected output size of each edge
        scale: range of size of the origin size cropped
        ratio: range of aspect ratio of the origin aspect ratio cropped
        interpolation: Default: BILINEAR
    """

    def __init__(self, size, scale=(0.08, 1.0), ratio=(3. / 4., 4. / 3.), interpolation='BILINEAR'):
        self.size = (size, size)
        self.interpolation = interpolation
        self.scale = scale
        self.ratio = ratio

    @staticmethod
    def get_params(img, scale, ratio):
        """Get parameters for ``crop`` for a random sized crop.

        Args:
            img (CV Image): Image to be cropped.
            scale (tuple): range of size of the origin size cropped
            ratio (tuple): range of aspect ratio of the origin aspect ratio cropped

        Returns:
            tuple: params (i, j, h, w) to be passed to ``crop`` for a random
                sized crop.
        """
        for attempt in range(10):
            area = img.shape[0] * img.shape[1]
            target_area = random.uniform(*scale) * area
            aspect_ratio = random.uniform(*ratio)

            w = int(round(math.sqrt(target_area * aspect_ratio)))
            h = int(round(math.sqrt(target_area / aspect_ratio)))

            if random.random() < 0.5:
                w, h = h, w

            if w <= img.shape[1] and h <= img.shape[0]:
                i = random.randint(0, img.shape[0] - h)
                j = random.randint(0, img.shape[1] - w)
                return i, j, h, w

        # Fallback
        w = min(img.shape[0], img.shape[1])
        i = (img.shape[0] - w) // 2
        j = (img.shape[1] - w) // 2
        return i, j, w, w

    def __call__(self, img):
        """
        Args:
            img (np.ndarray): Image to be cropped and resized.

        Returns:
            np.ndarray: Randomly cropped and resized image.
        """
        i, j, h, w = self.get_params(img, self.scale, self.ratio)

        return F.resized_crop(img, i, j, h, w, self.size, self.interpolation)

    def __repr__(self):
        interpolate_str = self.interpolation
        format_string = self.__class__.__name__ + '(size={0}'.format(self.size)
        format_string += ', scale={0}'.format(tuple(round(s, 4) for s in self.scale))
        format_string += ', ratio={0}'.format(tuple(round(r, 4) for r in self.ratio))
        format_string += ', interpolation={0})'.format(interpolate_str)
        return format_string


class RandomResizedCropDCT(object):
    """Crop the given CV Image to random size and aspect ratio.

    A crop of random size (default: of 0.08 to 1.0) of the original size and a random
    aspect ratio (default: of 3/4 to 4/3) of the original aspect ratio is made. This crop
    is finally resized to given size.
    This is popularly used to train the Inception networks.

    Args:
        size: expected output size of each edge
        scale: range of size of the origin size cropped
        ratio: range of aspect ratio of the origin aspect ratio cropped
    """

    def __init__(self, size, scale=(0.08, 1.0), ratio=(3. / 4., 4. / 3.), L=1, M=1, N=8,
                 interpolation='BILINEAR', upscale_method='raw'):
        self.size = (size, size)
        self.scale = scale
        self.ratio = ratio
        self.interpolation = interpolation
        self.upscale_method = upscale_method

        self.A1 = block_composition(L, N)
        self.A2 = block_composition(M, N)

    @staticmethod
    def get_params(img, scale, ratio):
        """Get parameters for ``crop`` for a random sized crop.

        Args:
            img (CV Image): Image to be cropped.
            scale (tuple): range of size of the origin size cropped
            ratio (tuple): range of aspect ratio of the origin aspect ratio cropped

        Returns:
            tuple: params (i, j, h, w) to be passed to ``crop`` for a random
                sized crop.
        """
        for attempt in range(10):
            area = img.shape[0] * img.shape[1]
            target_area = random.uniform(*scale) * area
            aspect_ratio = random.uniform(*ratio)

            w = int(round(math.sqrt(target_area * aspect_ratio)))
            h = int(round(math.sqrt(target_area / aspect_ratio)))

            if random.random() < 0.5:
                w, h = h, w

            if w <= img.shape[1] and h <= img.shape[0]:
                i = random.randint(0, img.shape[0] - h)
                j = random.randint(0, img.shape[1] - w)
                return i, j, h, w

        # Fallback
        w = min(img.shape[0], img.shape[1])
        i = (img.shape[0] - w) // 2
        j = (img.shape[1] - w) // 2
        return i, j, w, w

    def __call__(self, img):
        """
        Args:
            img (np.ndarray): Image to be cropped and resized.

        Returns:
            np.ndarray: Randomly cropped and resized image.
        """
        y, cb, cr = img[0], img[1], img[2]
        i, j, h, w = self.get_params(y, self.scale, self.ratio)

        if self.upscale_method == 'raw':
            y  = F.resized_crop(y, i, j, h, w, self.size, self.interpolation)
            cb = F.resized_crop(cb, i, j, h, w, self.size, self.interpolation)
            cr = F.resized_crop(cr, i, j, h, w, self.size, self.interpolation)
        else:
            y  = F.resized_crop_dct(y, i, j, h, w, self.size, A1=self.A1, A2=self.A2)
            cb = F.resized_crop_dct(cb, i, j, h, w, self.size, A1=self.A1, A2=self.A2)
            cr = F.resized_crop_dct(cr, i, j, h, w, self.size, A1=self.A1, A2=self.A2)

        return y, cb, cr

    def __repr__(self):
        format_string = self.__class__.__name__ + '(size={0}'.format(self.size)
        format_string += ', scale={0}'.format(tuple(round(s, 4) for s in self.scale))
        format_string += ', ratio={0}'.format(tuple(round(r, 4) for r in self.ratio))
        return format_string


class FiveCrop(object):
    """Crop the given CV Image into four corners and the central crop

    .. Note::
         This transform returns a tuple of images and there may be a mismatch in the number of
         inputs and targets your Dataset returns. See below for an example of how to deal with
         this.

    Args:
         size (sequence or int): Desired output size of the crop. If size is an ``int``
            instead of sequence like (h, w), a square crop of size (size, size) is made.

    Example:
         >>> transform = Compose([
         >>>    FiveCrop(size), # this is a list of CV Images
         >>>    Lambda(lambda crops: torch.stack([ToTensor()(crop) for crop in crops])) # returns a 4D tensor
         >>> ])
         >>> #In your test loop you can do the following:
         >>> input, target = batch # input is a 5d tensor, target is 2d
         >>> bs, ncrops, c, h, w = input.size()
         >>> result = model(input.view(-1, c, h, w)) # fuse batch size and ncrops
         >>> result_avg = result.view(bs, ncrops, -1).mean(1) # avg over crops
    """

    def __init__(self, size):
        self.size = size
        if isinstance(size, numbers.Number):
            self.size = (int(size), int(size))
        else:
            assert len(size) == 2, "Please provide only two dimensions (h, w) for size."
            self.size = size

    def __call__(self, img):
        return F.five_crop(img, self.size)

    def __repr__(self):
        return self.__class__.__name__ + '(size={0})'.format(self.size)


class TenCrop(object):
    """Crop the given CV Image into four corners and the central crop plus the flipped version of
    these (horizontal flipping is used by default)

    .. Note::
         This transform returns a tuple of images and there may be a mismatch in the number of
         inputs and targets your Dataset returns. See below for an example of how to deal with
         this.

    Args:
        size (sequence or int): Desired output size of the crop. If size is an
            int instead of sequence like (h, w), a square crop (size, size) is
            made.
        vertical_flip(bool): Use vertical flipping instead of horizontal

    Example:
         >>> transform = Compose([
         >>>    TenCrop(size), # this is a list of PIL Images
         >>>    Lambda(lambda crops: torch.stack([ToTensor()(crop) for crop in crops])) # returns a 4D tensor
         >>> ])
         >>> #In your test loop you can do the following:
         >>> input, target = batch # input is a 5d tensor, target is 2d
         >>> bs, ncrops, c, h, w = input.size()
         >>> result = model(input.view(-1, c, h, w)) # fuse batch size and ncrops
         >>> result_avg = result.view(bs, ncrops, -1).mean(1) # avg over crops
    """

    def __init__(self, size, vertical_flip=False):
        self.size = size
        if isinstance(size, numbers.Number):
            self.size = (int(size), int(size))
        else:
            assert len(size) == 2, "Please provide only two dimensions (h, w) for size."
            self.size = size
        self.vertical_flip = vertical_flip

    def __call__(self, img):
        return F.ten_crop(img, self.size, self.vertical_flip)

    def __repr__(self):
        return self.__class__.__name__ + '(size={0}, vertical_flip={1})'.format(self.size, self.vertical_flip)


class LinearTransformation(object):
    """Transform a tensor image with a square transformation matrix computed
    offline.

    Given transformation_matrix, will flatten the torch.*Tensor, compute the dot
    product with the transformation matrix and reshape the tensor to its
    original shape.

    Applications:
    - whitening: zero-center the data, compute the data covariance matrix
                 [D x D] with np.dot(X.T, X), perform SVD on this matrix and
                 pass it as transformation_matrix.

    Args:
        transformation_matrix (Tensor): tensor [D x D], D = C x H x W
    """

    def __init__(self, transformation_matrix):
        if transformation_matrix.size(0) != transformation_matrix.size(1):
            raise ValueError("transformation_matrix should be square. Got " +
                             "[{} x {}] rectangular matrix.".format(*transformation_matrix.size()))
        self.transformation_matrix = transformation_matrix

    def __call__(self, tensor):
        """
        Args:
            tensor (Tensor): Tensor image of size (C, H, W) to be whitened.

        Returns:
            Tensor: Transformed image.
        """
        if tensor.size(0) * tensor.size(1) * tensor.size(2) != self.transformation_matrix.size(0):
            raise ValueError("tensor and transformation matrix have incompatible shape." +
                             "[{} x {} x {}] != ".format(*tensor.size()) +
                             "{}".format(self.transformation_matrix.size(0)))
        flat_tensor = tensor.view(1, -1)
        transformed_tensor = torch.mm(flat_tensor, self.transformation_matrix)
        tensor = transformed_tensor.view(tensor.size())
        return tensor

    def __repr__(self):
        format_string = self.__class__.__name__ + '('
        format_string += (str(self.transformation_matrix.numpy().tolist()) + ')')
        return format_string


class ColorJitter(object):
    """Randomly change the brightness, contrast and saturation of an image.

    Args:
        brightness (float): How much to jitter brightness. brightness_factor
            is chosen uniformly from [max(0, 1 - brightness), 1 + brightness].
        contrast (float): How much to jitter contrast. contrast_factor
            is chosen uniformly from [max(0, 1 - contrast), 1 + contrast].
        saturation (float): How much to jitter saturation. saturation_factor
            is chosen uniformly from [max(0, 1 - saturation), 1 + saturation].
        hue(float): How much to jitter hue. hue_factor is chosen uniformly from
            [-hue, hue]. Should be >=0 and <= 0.5.
    """
    def __init__(self, brightness=0, contrast=0, saturation=0, hue=0):
        self.brightness = brightness
        self.contrast = contrast
        self.saturation = saturation
        self.hue = hue

    @staticmethod
    def get_params(brightness, contrast, saturation, hue):
        """Get a randomized transform to be applied on image.

        Arguments are same as that of __init__.

        Returns:
            Transform which randomly adjusts brightness, contrast and
            saturation in a random order.
        """
        transforms = []
        if brightness > 0:
            brightness_factor = random.uniform(max(0, 1 - brightness), 1 + brightness)
            transforms.append(Lambda(lambda img: F.adjust_brightness(img, brightness_factor)))

        if contrast > 0:
            contrast_factor = random.uniform(max(0, 1 - contrast), 1 + contrast)
            transforms.append(Lambda(lambda img: F.adjust_contrast(img, contrast_factor)))

        if saturation > 0:
            saturation_factor = random.uniform(max(0, 1 - saturation), 1 + saturation)
            transforms.append(Lambda(lambda img: F.adjust_saturation(img, saturation_factor)))

        if hue > 0:
            hue_factor = random.uniform(-hue, hue)
            transforms.append(Lambda(lambda img: F.adjust_hue(img, hue_factor)))

        random.shuffle(transforms)
        transform = Compose(transforms)

        return transform

    def __call__(self, img):
        """
        Args:
            img (np.ndarray): Input image.

        Returns:
            np.ndarray: Color jittered image.
        """
        transform = self.get_params(self.brightness, self.contrast,
                                    self.saturation, self.hue)
        return transform(img)

    def __repr__(self):
        format_string = self.__class__.__name__ + '('
        format_string += 'brightness={0}'.format(self.brightness)
        format_string += ', contrast={0}'.format(self.contrast)
        format_string += ', saturation={0}'.format(self.saturation)
        format_string += ', hue={0})'.format(self.hue)
        return format_string


class RandomRotation(object):
    """Rotate the image by angle.

    Args:
        degrees (sequence or float or int): Range of degrees to select from.
            If degrees is a number instead of sequence like (min, max), the range of degrees
            will be (-degrees, +degrees) clockwise order.
        resample ({CV.Image.NEAREST, CV.Image.BILINEAR, CV.Image.BICUBIC}, optional):
            An optional resampling filter.
            See http://pillow.readthedocs.io/en/3.4.x/handbook/concepts.html#filters
            If omitted, or if the image has mode "1" or "P", it is set to NEAREST.
        expand (bool, optional): Optional expansion flag.
            If true, expands the output to make it large enough to hold the entire rotated image.
            If false or omitted, make the output image the same size as the input image.
            Note that the expand flag assumes rotation around the center and no translation.
        center (2-tuple, optional): Optional center of rotation.
            Origin is the upper left corner.
            Default is the center of the image.
    """

    def __init__(self, degrees, resample='BILINEAR', expand=False, center=None):
        if isinstance(degrees, numbers.Number):
            if degrees < 0:
                raise ValueError("If degrees is a single number, it must be positive.")
            self.degrees = (-degrees, degrees)
        else:
            if len(degrees) != 2:
                raise ValueError("If degrees is a sequence, it must be of len 2.")
            self.degrees = degrees

        self.resample = resample
        self.expand = expand
        self.center = center

    @staticmethod
    def get_params(degrees):
        """Get parameters for ``rotate`` for a random rotation.

        Returns:
            sequence: params to be passed to ``rotate`` for random rotation.
        """
        angle = random.uniform(degrees[0], degrees[1])

        return angle

    def __call__(self, img):
        """
            img (np.ndarray): Image to be rotated.

        Returns:
            np.ndarray: Rotated image.
        """

        angle = self.get_params(self.degrees)

        return F.rotate(img, angle, self.resample, self.expand, self.center)

    def __repr__(self):
        format_string = self.__class__.__name__ + '(degrees={0}'.format(self.degrees)
        format_string += ', resample={0}'.format(self.resample)
        format_string += ', expand={0}'.format(self.expand)
        if self.center is not None:
            format_string += ', center={0}'.format(self.center)
        format_string += ')'
        return format_string


class RandomAffine(object):
    """Random affine transformation of the image keeping center invariant

    Args:
        degrees (sequence or float or int): Range of degrees to select from.
            If degrees is a number instead of sequence like (min, max), the range of degrees
            will be (-degrees, +degrees). Set to 0 to desactivate rotations.
        translate (tuple, optional): tuple of maximum absolute fraction for horizontal
            and vertical translations. For example translate=(a, b), then horizontal shift
            is randomly sampled in the range -img_width * a < dx < img_width * a and vertical shift is
            randomly sampled in the range -img_height * b < dy < img_height * b. Will not translate by default.
        scale (tuple, optional): scaling factor interval, e.g (a, b), then scale is
            randomly sampled from the range a <= scale <= b. Will keep original scale by default.
        shear (sequence or float or int, optional): Range of degrees to select from.
            If degrees is a number instead of sequence like (min, max), the range of degrees
            will be (-degrees, +degrees). Will not apply shear by default
        resample ({NEAREST, BILINEAR, BICUBIC}, optional): An optional resampling filter.
        fillcolor (int): Optional fill color for the area outside the transform in the output image. (Pillow>=5.0.0)
    """

    def __init__(self, degrees=0, translate=None, scale=None, shear=None, resample='BILINEAR', fillcolor=0):
        if isinstance(degrees, numbers.Number):
            if degrees < 0:
                raise ValueError("If degrees is a single number, it must be positive.")
            self.degrees = (-degrees, degrees)
        else:
            assert isinstance(degrees, (tuple, list)) and len(degrees) == 2, \
                "degrees should be a list or tuple and it must be of length 2."
            self.degrees = degrees

        if translate is not None:
            assert isinstance(translate, (tuple, list)) and len(translate) == 2, \
                "translate should be a list or tuple and it must be of length 2."
            for t in translate:
                if not (0.0 <= t <= 1.0):
                    raise ValueError("translation values should be between 0 and 1")
        self.translate = translate

        if scale is not None:
            assert isinstance(scale, (tuple, list)) and len(scale) == 2, \
                "scale should be a list or tuple and it must be of length 2."
            for s in scale:
                if s <= 0:
                    raise ValueError("scale values should be positive")
        self.scale = scale

        if shear is not None:
            if isinstance(shear, numbers.Number):
                if shear < 0:
                    raise ValueError("If shear is a single number, it must be positive.")
                self.shear = (-shear, shear)
            else:
                assert isinstance(shear, (tuple, list)) and len(shear) == 2, \
                    "shear should be a list or tuple and it must be of length 2."
                self.shear = shear
        else:
            self.shear = shear

        self.resample = resample
        self.fillcolor = fillcolor

    @staticmethod
    def get_params(degrees, translate, scale_ranges, shears, img_size):
        """Get parameters for affine transformation

        Returns:
            sequence: params to be passed to the affine transformation
        """
        angle = random.uniform(degrees[0], degrees[1])
        if translate is not None:
            max_dx = translate[0] * img_size[1]
            max_dy = translate[1] * img_size[0]
            translations = (np.round(random.uniform(-max_dx, max_dx)),
                            np.round(random.uniform(-max_dy, max_dy)))
        else:
            translations = (0, 0)

        if scale_ranges is not None:
            scale = random.uniform(scale_ranges[0], scale_ranges[1])
        else:
            scale = 1.0

        if shears is not None:
            shear = random.uniform(shears[0], shears[1])
        else:
            shear = 0.0

        return angle, translations, scale, shear

    def __call__(self, img):
        """
            img (CV Image): Image to be transformed.

        Returns:
            CV Image: Affine transformed image.
        """
        ret = self.get_params(self.degrees, self.translate, self.scale, self.shear, img.shape)
        return F.affine(img, *ret, resample=self.resample, fillcolor=self.fillcolor)

    def __repr__(self):
        s = '{name}(degrees={degrees}'
        if self.translate is not None:
            s += ', translate={translate}'
        if self.scale is not None:
            s += ', scale={scale}'
        if self.shear is not None:
            s += ', shear={shear}'
        if self.resample > 0:
            s += ', resample={resample}'
        if self.fillcolor != 0:
            s += ', fillcolor={fillcolor}'
        s += ')'
        d = dict(self.__dict__)
        d['resample'] = d['resample']
        return s.format(name=self.__class__.__name__, **d)


class Grayscale(object):
    """Convert image to grayscale.

    Args:
        num_output_channels (int): (1 or 3) number of channels desired for output image

    Returns:
        CV Image: Grayscale version of the input.
        - If num_output_channels == 1 : returned image is single channel
        - If num_output_channels == 3 : returned image is 3 channel with r == g == b

    """

    def __init__(self, num_output_channels=3):
        self.num_output_channels = num_output_channels

    def __call__(self, img):
        """
        Args:
            img (CV Image): Image to be converted to grayscale.

        Returns:
            CV Image: Randomly grayscaled image.
        """
        return F.to_grayscale(img, num_output_channels=self.num_output_channels)

    def __repr__(self):
        return self.__class__.__name__ + '(num_output_channels={0})'.format(self.num_output_channels)


class RandomGrayscale(object):
    """Randomly convert image to grayscale with a probability of p (default 0.1).

    Args:
        p (float): probability that image should be converted to grayscale.

    Returns:
        CV Image: Grayscale version of the input image with probability p and unchanged
        with probability (1-p).
        - If input image is 1 channel: grayscale version is 1 channel
        - If input image is 3 channel: grayscale version is 3 channel with r == g == b

    """

    def __init__(self, p=0.1):
        self.p = p

    def __call__(self, img):
        """
        Args:
            img (np.ndarray): Image to be converted to grayscale.

        Returns:
            np.ndarray: Randomly grayscaled image.
        """
        num_output_channels = 3
        if random.random() < self.p:
            return F.to_grayscale(img, num_output_channels=num_output_channels)
        return img

    def __repr__(self):
        return self.__class__.__name__ + '(p={0})'.format(self.p)


class RandomPerspective(object):
    """Random perspective transformation of the image keeping center invariant
        Args:
            fov(float): range of wide angle = 90+-fov
            anglex (sequence or float or int): Range of degrees rote around X axis to select from.
                If degrees is a number instead of sequence like (min, max), the range of degrees
                will be (-degrees, +degrees). Set to 0 to desactivate rotations.
            angley (sequence or float or int): Range of degrees rote around Y axis to select from.
                If degrees is a number instead of sequence like (min, max), the range of degrees
                will be (-degrees, +degrees). Set to 0 to desactivate rotations.
            anglez (sequence or float or int): Range of degrees rote around Z axis to select from.
                If degrees is a number instead of sequence like (min, max), the range of degrees
                will be (-degrees, +degrees). Set to 0 to desactivate rotations.

            shear (sequence or float or int): Range of degrees for shear rote around axis to select from.
                If degrees is a number instead of sequence like (min, max), the range of degrees
                will be (-degrees, +degrees). Set to 0 to desactivate rotations.
            translate (tuple, optional): tuple of maximum absolute fraction for horizontal
                and vertical translations. For example translate=(a, b), then horizontal shift
                is randomly sampled in the range -img_width * a < dx < img_width * a and vertical shift is
                randomly sampled in the range -img_height * b < dy < img_height * b. Will not translate by default.
            scale (tuple, optional): scaling factor interval, e.g (a, b), then scale is
                randomly sampled from the range a <= scale <= b. Will keep original scale by default.
            resample ({NEAREST, BILINEAR, BICUBIC}, optional): An optional resampling filter.
            fillcolor (int): Optional fill color for the area outside the transform in the output image. (Pillow>=5.0.0)
        """

    def __init__(self, fov=0, anglex=0, angley=0, anglez=0, shear=0,
                 translate=(0, 0), scale=(1, 1), resample='BILINEAR', fillcolor=(0, 0, 0)):

        assert all([isinstance(anglex, (tuple, list)) or anglex >= 0,
                    isinstance(angley, (tuple, list)) or angley >= 0,
                    isinstance(anglez, (tuple, list)) or anglez >= 0,
                    isinstance(shear, (tuple, list)) or shear >= 0]), \
            'All angles must be positive or tuple or list'
        assert 80 >= fov >= 0, 'fov should be in (0, 80)'
        self.fov = fov

        self.anglex = (-anglex, anglex) if isinstance(anglex, numbers.Number) else anglex
        self.angley = (-angley, angley) if isinstance(angley, numbers.Number) else angley
        self.anglez = (-anglez, anglez) if isinstance(anglez, numbers.Number) else anglez
        self.shear = (-shear, shear) if isinstance(shear, numbers.Number) else shear

        assert isinstance(translate, (tuple, list)) and len(translate) == 2, \
            "translate should be a list or tuple and it must be of length 2."
        assert all([0.0 <= i <= 1.0 for i in translate]), "translation values should be between 0 and 1"
        self.translate = translate

        if scale is not None:
            assert isinstance(scale, (tuple, list)) and len(scale) == 2, \
                "scale should be a list or tuple and it must be of length 2."
            assert all([s > 0 for s in scale]), "scale values should be positive"
        self.scale = scale

        self.resample = resample
        self.fillcolor = fillcolor

    @staticmethod
    def get_params(fov_range, anglex_ranges, angley_ranges, anglez_ranges, shear_ranges,
                   translate, scale_ranges,  img_size):
        """Get parameters for perspective transformation

        Returns:
            sequence: params to be passed to the perspective transformation
        """
        fov = 90 + random.uniform(-fov_range, fov_range)
        anglex = random.uniform(anglex_ranges[0], anglex_ranges[1])
        angley = random.uniform(angley_ranges[0], angley_ranges[1])
        anglez = random.uniform(anglez_ranges[0], anglez_ranges[1])
        shear = random.uniform(shear_ranges[0], shear_ranges[1])

        max_dx = translate[0] * img_size[1]
        max_dy = translate[1] * img_size[0]
        translations = (np.round(random.uniform(-max_dx, max_dx)),
                        np.round(random.uniform(-max_dy, max_dy)))

        scale = (random.uniform(1 / scale_ranges[0], scale_ranges[0]),
                 random.uniform(1 / scale_ranges[1], scale_ranges[1]))

        return fov, anglex, angley, anglez, shear, translations, scale

    def __call__(self, img):
        """
            img (np.ndarray): Image to be transformed.

        Returns:
            np.ndarray: Affine transformed image.
        """
        ret = self.get_params(self.fov, self.anglex, self.angley, self.anglez, self.shear,
                              self.translate, self.scale, img.shape)
        return F.perspective(img, *ret, resample=self.resample, fillcolor=self.fillcolor)

    def __repr__(self):
        s = '{name}(degrees={degrees}'
        if self.translate is not None:
            s += ', translate={translate}'
        if self.scale is not None:
            s += ', scale={scale}'
        if self.shear is not None:
            s += ', shear={shear}'
        if self.resample > 0:
            s += ', resample={resample}'
        if self.fillcolor != 0:
            s += ', fillcolor={fillcolor}'
        s += ')'
        d = dict(self.__dict__)
        d['resample'] = d['resample']
        return s.format(name=self.__class__.__name__, **d)


class RandomAffine6(object):
    """Random affine transformation of the image keeping center invariant

    Args:
        anglez (sequence or float or int): Range of rotate to select from.
            If degrees is a number instead of sequence like (min, max), the range of degrees
            will be (-anglez, +anglez). Set to 0 to desactivate rotations.
        shear (sequence or float or int): Range of shear to select from.
            If degrees is a number instead of sequence like (min, max), the range of degrees
            will be (-shear, +shear). Set to 0 to desactivate shear.
        translate (tuple, optional): tuple of maximum absolute fraction for horizontal
            and vertical translations. For example translate=(a, b), then horizontal shift
            is randomly sampled in the range -img_width * a < dx < img_width * a and vertical shift is
            randomly sampled in the range -img_height * b < dy < img_height * b. Will not translate by default.
        scale (tuple, optional): scaling factor interval, e.g (a, b), then scale is
            randomly sampled from the range a <= scale <= b. Will keep original scale by default.
        resample ({NEAREST, BILINEAR, BICUBIC}, optional): An optional resampling filter.
        fillcolor (int): Optional fill color for the area outside the transform in the output image. (Pillow>=5.0.0)
    """

    def __init__(self, anglez=0, shear=0, translate=(0, 0), scale=(1, 1),
                 resample='BILINEAR', fillcolor=(0, 0, 0)):
        if isinstance(anglez, numbers.Number):
            if anglez < 0:
                raise ValueError("If anglez is a single number, it must be positive.")
            self.anglez = (-anglez, anglez)
        else:
            assert isinstance(anglez, (tuple, list)) and len(anglez) == 2, \
                "anglez should be a list or tuple and it must be of length 2."
            self.anglez = anglez

        if isinstance(shear, numbers.Number):
            if shear < 0:
                raise ValueError("If shear is a single number, it must be positive.")
            self.shear = (-shear, shear)
        else:
            assert isinstance(shear, (tuple, list)) and len(shear) == 2, \
                "shear should be a list or tuple and it must be of length 2."
            self.shear = shear

        if translate is not None:
            assert isinstance(translate, (tuple, list)) and len(translate) == 2, \
                "translate should be a list or tuple and it must be of length 2."
            for t in translate:
                if not (0.0 <= t <= 1.0):
                    raise ValueError("translation values should be between 0 and 1")
        self.translate = translate

        if scale is not None:
            assert isinstance(scale, (tuple, list)) and len(scale) == 2, \
                "scale should be a list or tuple and it must be of length 2."
            for s in scale:
                if s <= 0:
                    raise ValueError("scale values should be positive")
        self.scale = scale
        self.resample = resample
        self.fillcolor = fillcolor

    @staticmethod
    def get_params(img_size, anglez_range=(0, 0), shear_range=(0, 0),
                   translate=(0, 0), scale_ranges=(1, 1)):
        """Get parameters for affine transformation

        Returns:
            sequence: params to be passed to the affine transformation
        """
        angle = random.uniform(anglez_range[0], anglez_range[1])
        shear = random.uniform(shear_range[0], shear_range[1])

        max_dx = translate[0] * img_size[1]
        max_dy = translate[1] * img_size[0]
        translations = (np.round(random.uniform(-max_dx, max_dx)),
                        np.round(random.uniform(-max_dy, max_dy)))

        scale = (random.uniform(1 / scale_ranges[0], scale_ranges[0]),
                 random.uniform(1 / scale_ranges[1], scale_ranges[1]))

        return angle, shear, translations, scale

    def __call__(self, img):
        """
            img (np.ndarray): Image to be transformed.

        Returns:
            np.ndarray: Affine transformed image.
        """
        ret = self.get_params(img.shape, self.anglez, self.shear, self.translate, self.scale)
        return F.affine6(img, *ret, resample=self.resample, fillcolor=self.fillcolor)

    def __repr__(self):
        s = '{name}(degrees={degrees}'
        if self.translate is not None:
            s += ', translate={translate}'
        if self.scale is not None:
            s += ', scale={scale}'
        if self.shear is not None:
            s += ', shear={shear}'
        if self.resample > 0:
            s += ', resample={resample}'
        if self.fillcolor != 0:
            s += ', fillcolor={fillcolor}'
        s += ')'
        d = dict(self.__dict__)
        d['resample'] = d['resample']
        return s.format(name=self.__class__.__name__, **d)


class RandomGaussianNoise(object):
    """Applying gaussian noise on the given CV Image randomly with a given probability.

        Args:
            p (float): probability of the image being noised. Default value is 0.5
        """

    def __init__(self, p=0.5, mean=0, std=0.1):
        assert isinstance(mean, numbers.Number) and mean >= 0, 'mean should be a positive value'
        assert isinstance(std, numbers.Number) and std >= 0, 'std should be a positive value'
        assert isinstance(p, numbers.Number) and p >= 0, 'p should be a positive value'
        self.p = p
        self.mean = mean
        self.std = std

    @staticmethod
    def get_params(mean, std):
        """Get parameters for gaussian noise

        Returns:
            sequence: params to be passed to the affine transformation
        """
        mean = random.uniform(-mean, mean)
        std = random.uniform(-std, std)

        return mean, std

    def __call__(self, img):
        """
        Args:
            img (np.ndarray): Image to be noised.

        Returns:
            np.ndarray: Randomly noised image.
        """
        if random.random() < self.p:
            return F.gaussian_noise(img, mean=self.mean, std=self.std)
        return img

    def __repr__(self):
        return self.__class__.__name__ + '(p={})'.format(self.p)


class RandomPoissonNoise(object):
    """Applying Poisson noise on the given CV Image randomly with a given probability.

        Args:
            p (float): probability of the image being noised. Default value is 0.5
        """

    def __init__(self, p=0.5):
        assert isinstance(p, numbers.Number) and p >= 0, 'p should be a positive value'
        self.p = p

    def __call__(self, img):
        """
        Args:
            img (np.ndarray): Image to be noised.

        Returns:
            np.ndarray: Randomly noised image.
        """
        if random.random() < self.p:
            return F.poisson_noise(img)
        return img

    def __repr__(self):
        return self.__class__.__name__ + '(p={})'.format(self.p)


class RandomSPNoise(object):
    """Applying salt and pepper noise on the given CV Image randomly with a given probability.

        Args:
            p (float): probability of the image being noised. Default value is 0.5
        """

    def __init__(self, p=0.5, prob=0.1):
        assert isinstance(p, numbers.Number) and p >= 0, 'p should be a positive value'
        assert isinstance(prob, numbers.Number) and prob >= 0, 'p should be a positive value'
        self.p = p
        self.prob = prob

    def __call__(self, img):
        """
        Args:
            img (np.ndarray): Image to be noised.

        Returns:
            np.ndarray: Randomly noised image.
        """
        if random.random() < self.p:
            return F.salt_and_pepper(img, self.prob)
        return img

    def __repr__(self):
        return self.__class__.__name__ + '(p={})'.format(self.p)
