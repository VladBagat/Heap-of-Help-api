from Ranking.graph_builder import GraphBuilder, Node
from Ranking.graph_traversal import GraphSearcher
from typing import List


class RankingAlgorithm:
    def __init__(self):    
        self.__search = GraphSearcher() 
        self.__search.graph = GraphBuilder().graph 
        # This is currently a de-nesting approach.
        # Maybe moving builder into traversal is better but that's later
        
        
    def calculate_content_score(self, content_tags: List[str], user_tags: List[str]):
        """
        Calculate content score based on tags, user interests, and interaction statistics.
        Returns both overall score and subscores for transparency.
        """
        scores = {
            'tag_relevance': self._calculate_tag_relevance(content_tags, user_tags),
            'popularity': 0,
            'freshness': 0
        }

        # Weighted combination of scores
        scores['final_score'] = (
            scores['tag_relevance'] * 1 +
            scores['popularity'] * 0.0 +
            scores['freshness'] * 0.0 
        )

        return scores
    
    def _calculate_tag_relevance(self, user_tags: List[str], content_tags: List[str]):
        content_set = set(content_tags)
        user_set = set(user_tags)
        normalization = len(user_tags)
        
        if not user_set or not content_set:
            return 0
    
        matched_tags = content_set.intersection(user_set)
                                    
        user_set.difference_update(matched_tags)
        content_set.difference_update(matched_tags)
        
        score = len(matched_tags)
                                    
        for user_tag in user_set:
            best_score = 0
            for content_tag in content_set: 
                result = self.__search.rank(user_tag, content_tag)
                if result and result > best_score:
                    best_score = result
            score += best_score
                

        normalized_relevance = score / normalization
        return normalized_relevance      
