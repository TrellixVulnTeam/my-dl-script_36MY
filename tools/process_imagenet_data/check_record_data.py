import tensorflow as tf
import os

os.environ['CUDA_VISIBLE_DEVICES'] = ''

# Record Data Structure
# {
#     'image/height': _int64_feature(height),
#     'image/width': _int64_feature(width),
#     'image/colorspace': _bytes_feature(colorspace),
#     'image/channels': _int64_feature(channels),
#     'image/class/label': _int64_feature(label),
#     'image/class/synset': _bytes_feature(synset),
#     'image/class/text': _bytes_feature(human),
#     'image/object/bbox/xmin': _float_feature(xmin),
#     'image/object/bbox/xmax': _float_feature(xmax),
#     'image/object/bbox/ymin': _float_feature(ymin),
#     'image/object/bbox/ymax': _float_feature(ymax),
#     'image/object/bbox/label': _int64_feature([label] * len(xmin)),
#     'image/format': _bytes_feature(image_format),
#     'image/filename': _bytes_feature(os.path.basename(filename)),
#     'image/encoded': _bytes_feature(image_buffer)
# }

def parse_example_proto(example_serialized):
  """Parses an Example proto containing a training example of an image.

  The output of the build_image_data.py image preprocessing script is a dataset
  containing serialized Example protocol buffers. Each Example proto contains
  the following fields:

    image/height: 462
    image/width: 581
    image/colorspace: 'RGB'
    image/channels: 3
    image/class/label: 615
    image/class/synset: 'n03623198'
    image/class/text: 'knee pad'
    image/object/bbox/xmin: 0.1
    image/object/bbox/xmax: 0.9
    image/object/bbox/ymin: 0.2
    image/object/bbox/ymax: 0.6
    image/object/bbox/label: 615
    image/format: 'JPEG'
    image/filename: 'ILSVRC2012_val_00041207.JPEG'
    image/encoded: <JPEG encoded string>

  Args:
    example_serialized: scalar Tensor tf.string containing a serialized
      Example protocol buffer.

  Returns:
    image_buffer: Tensor tf.string containing the contents of a JPEG file.
    label: Tensor tf.int32 containing the label.
    bbox: 3-D float Tensor of bounding boxes arranged [1, num_boxes, coords]
      where each coordinate is [0, 1) and the coordinates are arranged as
      [ymin, xmin, ymax, xmax].
    text: Tensor tf.string containing the human-readable label.
  """
  # Dense features in Example proto.
  feature_map = {
      'image/encoded': tf.FixedLenFeature([], dtype=tf.string,
                                          default_value=''),
      'image/class/label': tf.FixedLenFeature([1], dtype=tf.int64,
                                              default_value=-1),
      'image/class/text': tf.FixedLenFeature([], dtype=tf.string,
                                             default_value=''),
      'image/height': tf.FixedLenFeature([1], dtype=tf.int64,
                                              default_value=-1),
      'image/width': tf.FixedLenFeature([1], dtype=tf.int64,
                                              default_value=-1)
  }
  sparse_float32 = tf.VarLenFeature(dtype=tf.float32)
  # Sparse features in Example proto.
  feature_map.update(
      {k: sparse_float32 for k in ['image/object/bbox/xmin',
                                   'image/object/bbox/ymin',
                                   'image/object/bbox/xmax',
                                   'image/object/bbox/ymax']})

  features = tf.parse_single_example(example_serialized, feature_map)
  label = tf.cast(features['image/class/label'], dtype=tf.int32)

  xmin = tf.expand_dims(features['image/object/bbox/xmin'].values, 0)
  ymin = tf.expand_dims(features['image/object/bbox/ymin'].values, 0)
  xmax = tf.expand_dims(features['image/object/bbox/xmax'].values, 0)
  ymax = tf.expand_dims(features['image/object/bbox/ymax'].values, 0)

  # Note that we impose an ordering of (y, x) just to make life difficult.
  bbox = tf.concat(axis=0, values=[ymin, xmin, ymax, xmax])

  # Force the variable number of bounding boxes into the shape
  # [1, num_boxes, coords].
  bbox = tf.expand_dims(bbox, 0)
  bbox = tf.transpose(bbox, [0, 2, 1])

  return features['image/encoded'], label, features['image/class/text'], features['image/height'], features['image/width']

filename = ["record-data/train-00000-of-01024"]
dataset = tf.data.TFRecordDataset(filename)

dataset = dataset.map(parse_example_proto)
iterator = dataset.make_initializable_iterator()

sess = tf.Session()

sess.run(iterator.initializer)

count = 0

try:
    while (True):
        sess.run(iterator.get_next())
        count += 1
except tf.errors.OutOfRangeError:
    print(count)
    print("Done")
