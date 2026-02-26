import pytest
from unittest.mock import MagicMock, patch
import numpy as np
import torch
from vieneu.standard import VieNeuTTS
from vieneu.remote import RemoteVieNeuTTS

@pytest.fixture
def mock_codec():
    codec = MagicMock()
    codec.sample_rate = 24000
    codec.device = "cpu"
    # Mock encode_code to return a tensor of codes
    codec.encode_code.return_value = torch.zeros((1, 1, 10), dtype=torch.long)
    # Mock decode_code to return a tensor of audio
    codec.decode_code.return_value = torch.zeros((1, 1, 4800), dtype=torch.float32)
    return codec

@pytest.fixture
def mock_backbone():
    backbone = MagicMock()
    backbone.device = torch.device("cpu")
    backbone.to.return_value = backbone
    # Mock generate for torch backend
    backbone.generate.return_value = torch.tensor([[0, 1, 2, 3]]) # Dummy output tokens
    # Mock llama-cpp call
    backbone.return_value = {"choices": [{"text": "<|speech_1|><|speech_2|>"}]}
    return backbone

@pytest.fixture
def mock_tokenizer():
    tokenizer = MagicMock()
    tokenizer.convert_tokens_to_ids.return_value = 1
    tokenizer.encode.return_value = [1, 2, 3]
    tokenizer.decode.return_value = "<|speech_1|><|speech_2|>"
    return tokenizer

def test_vieneu_tts_init(mock_codec, mock_backbone, mock_tokenizer):
    with patch("vieneu.standard.NeuCodec.from_pretrained", return_value=mock_codec), \
         patch("vieneu.standard.DistillNeuCodec.from_pretrained", return_value=mock_codec), \
         patch("transformers.AutoTokenizer.from_pretrained", return_value=mock_tokenizer), \
         patch("transformers.AutoModelForCausalLM.from_pretrained", return_value=mock_backbone):

        tts = VieNeuTTS(backbone_repo="some/repo", backbone_device="cpu")
        assert tts.backbone is not None
        assert tts.codec is not None

def test_vieneu_tts_infer(mock_codec, mock_backbone, mock_tokenizer):
    with patch("vieneu.standard.NeuCodec.from_pretrained", return_value=mock_codec), \
         patch("vieneu.standard.DistillNeuCodec.from_pretrained", return_value=mock_codec), \
         patch("transformers.AutoTokenizer.from_pretrained", return_value=mock_tokenizer), \
         patch("transformers.AutoModelForCausalLM.from_pretrained", return_value=mock_backbone):

        tts = VieNeuTTS(backbone_repo="some/repo", backbone_device="cpu")

        # Mocking phonemize_with_dict to avoid espeak dependency issues in some envs
        with patch("vieneu.standard.phonemize_with_dict", return_value="phonemes"):
            audio = tts.infer("Xin chào", ref_codes=[1, 2, 3], ref_text="Chào")
            assert isinstance(audio, np.ndarray)
            assert len(audio) > 0

def test_remote_vieneu_tts_infer(mock_codec):
    with patch("vieneu.standard.DistillNeuCodec.from_pretrained", return_value=mock_codec):
        tts = RemoteVieNeuTTS(api_base="http://mock-api", model_name="mock-model")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "<|speech_1|><|speech_2|>"}}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_response), \
             patch("vieneu.remote.phonemize_with_dict", return_value="phonemes"):
            audio = tts.infer("Xin chào", ref_codes=[1, 2, 3], ref_text="Chào")
            assert isinstance(audio, np.ndarray)
            assert len(audio) > 0
