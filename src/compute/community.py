import json


# DiscreteContinuousCoupled(item_id='260', community_score=4.437363166878454, user_score=4.402113049947503, community_label=1, user_label=1)
class DiscreteContinuousCoupled(dict):
	item_id:str
	community_score:float
	user_score:float
	community_label:int
	user_label:int

	def __init_subclass__(cls) -> None:
		return super().__init_subclass__()

def get_discrete_continuous_coupled() -> list:
	mylst:list
	with open('./compute/dummy_outputs.txt', 'r') as f:
		mylst = eval(f.read())

	return mylst


if __name__ == '__main__':
	mylst = []
	with open('dummy_outputs.txt', 'r') as f:
		mylst = eval(f.read())