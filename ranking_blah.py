from dataclasses import dataclass
from typing import Dict, List, Set
from collections import defaultdict
import math

@dataclass
class TagWeight:
    category: str  # e.g., 'programming_language', 'field', 'framework'
    weight: float  # base weight for this category
    depth: int    # hierarchy level (e.g., CS->Backend->Python)

class ContentScoring:
    def __init__(self):
        self.tag_weights = {
            'field': TagWeight('field', 1.0, 1),            # CS, Data Science, etc.
            'programming_language': TagWeight('programming_language', 0.8, 2),  # Python, Java, etc.
            'framework': TagWeight('framework', 0.6, 3),     # React, Django, etc.
            'concept': TagWeight('concept', 0.7, 2),        # Algorithms, Design Patterns
        }
        
        # Example tag relationships (simplified hierarchical structure)
        self.tag_relationships = {
            'backend': {'python', 'java', 'nodejs'},
            'python': {'django', 'flask', 'fastapi'},
            'java': {'spring', 'hibernate'},
            'frontend': {'javascript', 'typescript'},
            'javascript': {'react', 'vue', 'angular'}
        }

        # Tag category mappings
        self.tag_categories = {
            'field': {'backend', 'frontend', 'data_science', 'mobile', 'devops'},
            'programming_language': {'python', 'java', 'javascript', 'typescript', 'kotlin', 'swift'},
            'framework': {'django', 'flask', 'spring', 'react', 'vue', 'angular', 'fastapi'},
            'concept': {'algorithms', 'design_patterns', 'testing', 'security', 'performance'}
        }

    def _tag_belongs_to_category(self, tag: str, category: str) -> bool:
        """
        Check if a tag belongs to a specific category
        
        Args:
            tag: The tag to check
            category: The category to check against
            
        Returns:
            bool: True if the tag belongs to the category, False otherwise
        """
        # Direct category membership
        if tag in self.tag_categories.get(category, set()):
            return True
            
        # Check hierarchical relationships
        if category == 'framework':
            # Check if tag is a framework of any programming language
            for lang_frameworks in self.tag_relationships.values():
                if tag in lang_frameworks:
                    return True
        
        # For programming languages, check if they have frameworks
        if category == 'programming_language':
            return tag in self.tag_relationships
            
        # For fields, check if they're parent nodes in relationships
        if category == 'field':
            return tag in self.tag_categories['field']
            
        return False

    def calculate_content_score(self, 
                              content_tags: Set[str], 
                              user_interests: Set[str], 
                              interaction_stats: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate content score based on tags, user interests, and interaction statistics
        Returns both overall score and subscores for transparency
        """
        scores = {
            'tag_relevance': self._calculate_tag_relevance(content_tags, user_interests),
            'popularity': self._normalize_popularity(interaction_stats),
            'freshness': interaction_stats.get('recency_score', 0.5),
            'depth_score': self._calculate_depth_coverage(content_tags)
        }
        
        # Weighted combination of scores
        scores['final_score'] = (
            scores['tag_relevance'] * 0.4 +
            scores['popularity'] * 0.3 +
            scores['freshness'] * 0.2 +
            scores['depth_score'] * 0.1
        )
        
        return scores

    def _calculate_tag_relevance(self, content_tags: Set[str], user_interests: Set[str]) -> float:
        relevance_score = 0.0
        matched_tags = content_tags.intersection(user_interests)
        
        for tag in matched_tags:
            # Find the category of the tag
            for category, weight_info in self.tag_weights.items():
                if self._tag_belongs_to_category(tag, category):
                    # Apply category weight and consider tag relationships
                    base_score = weight_info.weight
                    relationship_bonus = self._calculate_relationship_bonus(tag, content_tags)
                    relevance_score += base_score * (1 + relationship_bonus)
        
        return min(1.0, relevance_score / max(len(content_tags), 1))

    def _calculate_depth_coverage(self, content_tags: Set[str]) -> float:
        """Calculate how well the content covers related concepts at different levels"""
        depth_counts = defaultdict(int)
        
        for tag in content_tags:
            for category, weight_info in self.tag_weights.items():
                if self._tag_belongs_to_category(tag, category):
                    depth_counts[weight_info.depth] += 1
        
        # Reward content that covers multiple levels
        depth_score = sum(count * (1/depth) for depth, count in depth_counts.items())
        return min(1.0, depth_score / 5)  # Normalize to 0-1

    def _calculate_relationship_bonus(self, tag: str, content_tags: Set[str]) -> float:
        """Calculate bonus for related tags being present"""
        if tag in self.tag_relationships:
            related_tags = self.tag_relationships[tag]
            matches = len(related_tags.intersection(content_tags))
            return min(0.5, matches * 0.1)  # Cap the bonus at 0.5
        return 0.0

    @staticmethod
    def _normalize_popularity(stats: Dict[str, float]) -> float:
        """Normalize popularity metrics to 0-1 range"""
        views = stats.get('views', 0)
        likes = stats.get('likes', 0)
        shares = stats.get('shares', 0)
        
        # Log transformation to handle varying scales
        normalized_score = (
            math.log1p(views) * 0.4 +
            math.log1p(likes) * 0.4 +
            math.log1p(shares) * 0.2
        ) / math.log1p(1000)  # Normalize assuming 1000 is a high interaction count
        
        return min(1.0, normalized_score)