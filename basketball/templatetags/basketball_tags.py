from django import template
from basketball import models as bmodels
from django.db.models import Sum, Q
from collections import OrderedDict
register = template.Library()

@register.inclusion_tag('box_score.html')
def box_score(statlines,bgcolor="white"):
        team_totals = {}
        for play in bmodels.ALL_PLAY_TYPES:
            if play[0] not in ['sub_out','sub_in']:
                x = statlines.exclude(player__first_name__contains='Team').aggregate(Sum(play[0]))
                team_totals.update(x)
        team_totals.update(statlines.aggregate(Sum('points'),Sum('total_rebounds')))
        return {'statlines': statlines.exclude(player__first_name__contains='Team'),
                'team': statlines.get(player__first_name__contains='Team'),
                'team_totals':team_totals,
                'bgcolor':bgcolor}

@register.inclusion_tag('player_box_score.html')
def player_box_score(statlines,bgcolor="white"):
	return {'statlines': statlines,'bgcolor':bgcolor}

def top_stat_players(game_type,stat,excluded_pks):
    players = bmodels.Player.objects.all().exclude(Q(first_name__contains="Team")|Q(pk__in=excluded_pks))
    player_list = []
    for player in players:
        result = player.statline_set.filter(game__game_type=game_type).aggregate(Sum(stat),Sum('off_pos'))
        if result['off_pos__sum'] is not 0:
            percentage = (result[stat + '__sum']/result['off_pos__sum']) * 100
        else:
            percentage = 0.0
        player_list.append((player.first_name,percentage))
    return sorted(player_list,key=lambda x: x[1],reverse=True)

@register.inclusion_tag('lb_5on5_possessions.html')
def lb_five_on_five_pos():
    
    players = bmodels.Player.objects.all().exclude(first_name__contains="Team")

    #exclude players that dont meet the minimum 100 possessions requirement
    excluded_pks = []
    for player in players:
        pos_count = player.statline_set.all().aggregate(Sum('off_pos'))
        if pos_count['off_pos__sum'] < 100:
            excluded_pks.append(player.pk)

    players = players.exclude(pk__in=excluded_pks)

    dreb = top_stat_players('5v5','dreb',excluded_pks)
    oreb = top_stat_players('5v5','oreb',excluded_pks)  
    total_rebounds = top_stat_players('5v5','total_rebounds',excluded_pks)
    asts = top_stat_players('5v5','asts',excluded_pks)
    pot_ast = top_stat_players('5v5','pot_ast',excluded_pks)
    stls = top_stat_players('5v5','stls',excluded_pks)
    to = top_stat_players('5v5','to',excluded_pks)
    points = top_stat_players('5v5','points',excluded_pks)

    #these need special attention
    fgm_percent = []
    for player in players:
        result = player.statline_set.filter(game__game_type='5v5').aggregate(Sum('fgm'),Sum('fga'),Sum('off_pos'))
        if result['fga__sum'] is not 0 and result['off_pos__sum'] is not 0:
            percentage = ( (result['fgm__sum']/result['fga__sum']) / result['off_pos__sum'] ) * 100
        else:
            percentage = 0.0
        fgm_percent.append((player.first_name,percentage))
    fgm_percent = sorted(fgm_percent,key=lambda x: x[1],reverse=True)
   
    three_percent = []
    for player in players:
        result = player.statline_set.filter(game__game_type='5v5').aggregate(Sum('threepm'),Sum('threepa'),Sum('off_pos'))
        if result['threepa__sum'] is not 0 and result['off_pos__sum'] is not 0:
            percentage = ( (result['threepm__sum']/result['threepa__sum']) / result['off_pos__sum'] ) * 100
        else:
            percentage = 0.0
        three_percent.append((player.first_name,percentage))
    three_percent = sorted(three_percent,key=lambda x: x[1],reverse=True)

    dreb_percent = []
    for player in players:
        result = player.statline_set.filter(game__game_type='5v5').aggregate(Sum('dreb'),Sum('total_rebounds'),Sum('def_pos'))
        if result['total_rebounds__sum'] is not 0 and result['def_pos__sum'] is not 0:
            percentage = ( (result['dreb__sum']/result['total_rebounds__sum']) / result['def_pos__sum'] ) * 100
        else:
            percentage = 0.0
        dreb_percent.append((player.first_name,percentage))
    dreb_percent = sorted(dreb_percent,key=lambda x: x[1],reverse=True)

    context = {
            "dreb":dreb[:5],
            "oreb":oreb[:5],
            "total_rebounds":total_rebounds[:5],
            "asts":asts[:5],
            "pot_ast":pot_ast[:5],
            "stls":stls[:5],
            "to":to[:5],
            "points":points[:5],
            "fgm_percent":fgm_percent[:5],
            "three_percent":three_percent[:5],
            "dreb_percent":dreb_percent[:5],
    }
    return context

@register.inclusion_tag('lb_totals.html')
def lb_5on5_totals():
    
    players = bmodels.Player.objects.all().exclude(first_name__contains="Team").order_by('first_name')
    player_dict = OrderedDict()
    for player in players:
        player_total = player.statline_set.filter(game__game_type='5v5').aggregate(\
                Sum('fga'),Sum('fgm'),Sum('threepm'),Sum('threepa'),\
                Sum('dreb'),Sum('oreb'),Sum('total_rebounds'),Sum('asts'),\
                Sum('pot_ast'),Sum('blk'),Sum('ba'),Sum('stls'),\
                Sum('to'),Sum('fd'),Sum('pf'),Sum('def_pos'),\
                Sum('off_pos'),Sum('points'))
        player_dict[player.get_full_name()] = player_total

    context = {
            'player_dict':player_dict,
    }
    return context

@register.inclusion_tag('top_stat_table.html')
def top_players_table(player_list,title,bgcolor='white'):
    return {'player_list':player_list,'title':title,'bgcolor':bgcolor}
