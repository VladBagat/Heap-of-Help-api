from Ranking.graph_builder import GraphBuilder, Node
from Ranking.graph_traversal import GraphSearcher


class RankingAlgorithm:
    def __init__(self):    
        self.__search = GraphSearcher() 
        self.__search.graph = GraphBuilder().graph 
        # This is currently a de-nesting approach.
        # Maybe moving builder into traversal is better but that's later
        
        
    def calculate_content_score(self, content_tags, user_tags):
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
    
    def _calculate_tag_relevance(self, content_tags, user_tags):
        content_tags = set(content_tags)
        user_tags = set(user_tags)
        tag_relevance = 0
        per_tag_relevance = 1/len(user_tags)
    
        matched_tags = content_tags.intersection(user_tags)
                
        user_tags.difference_update(matched_tags)
        content_tags.difference_update(matched_tags)
                    
        for user_tag in user_tags:
            for content_tag in content_tags: 
                result = self.__search.rank(user_tag, content_tag)
                if result:
                    tag_relevance += per_tag_relevance * result #This might under/over calculate stuff
                
        tag_relevance += per_tag_relevance * len(matched_tags)
        
        return tag_relevance
        
       

    
if __name__ == "__main__":
    ra = RankingAlgorithm()
    
    print(ra.calculate_content_score(['Java', 'Distributed Systems', 'Computer Hardware/Architectures'], ['Viewstamped Replication', 'RISC-V', 'Java']))