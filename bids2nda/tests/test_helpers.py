from ..main import cosine_to_orientation


def test_cosine_to_orientation():
    assert cosine_to_orientation([0.9, -0.03, -0.1, 0.03, 0.9, 0.1]) == 'Axial'
    assert cosine_to_orientation([0, 0.9, 0.1, 0.03, 0.1, -0.9]) == 'Sagittal'


