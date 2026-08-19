from pmu.types.enum import BetType
from pmu.types.types import CourseIdentifier


def is_bet_won(course_identifier: CourseIdentifier, bet_type: BetType, combinaison: [int]):
    '''
    TODO: Implémenter cette fonction avec gestion d'erreur.\n
    1. Récupération du rapport final de la course via l'API PMU\n
    2. Si il est disponible, on recherche l'élement du tableau avec `typePari` égal à `bet_type`\n
    3. Dans l'élement détecté, on vérifie si le pari est annulé `"rembourse": true\n
    4. Si le pari n'est pas annulé, on recherche dans le tableau d'objets à la clé `rapports` si notre combinaison correspond à la clé `combinaison`.
    '''
    return