from ..models.bertclass import BERTClass
import torch
from transformers import BertTokenizer, BertModel


def get_model():
    # import bert model
    model = BERTClass()
    model_weights = torch.load("/app/bias_model/best_model_ba_12_wd.pt", map_location=torch.device('cpu'))['state_dict']
    model.load_state_dict(model_weights)
    device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
    model.to(device)
    model.eval()
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

    return {"device":device, "model":model, "tokenizer":tokenizer}