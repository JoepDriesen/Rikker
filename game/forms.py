from django import forms
from game.models import Bid

class MakeBidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['bid']
        
    def __init__(self, *args, **kwargs):
        current_round = kwargs.get('current_round', None)
        if 'current_round' in kwargs:
            del kwargs['current_round']
            
        result = super(MakeBidForm, self).__init__(*args, **kwargs)
        
        if current_round is not None:
            highest_bid = current_round.temp_highest_bid()
            if highest_bid is None:
                highest_bid = -1
            else:
                highest_bid = highest_bid.bid
            
            choices = []
            lowest_rik = False
            for bid in Bid.BIDS:
                if bid[0] is Bid.PASS:
                    choices.append(bid)
                elif bid[0] > highest_bid:
                    if Bid.bid_is_rik(bid[0]):
                        if not lowest_rik:
                            choices.append(bid)
                            lowest_rik = True
                    else:
                        choices.append(bid)
                
            self.fields['bid'].choices = choices
        return result

class PickTrumpSuitAndMateForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['trump_suit', 'mate_suit']

class PickTrumpSuitForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['trump_suit']