#!/usr/bin/env python3
"""
🜂 KISWARM7.0 - Module m102: Integration Hooks
🜃 AI Self-Evolution Bridge - Memory Integration Across Sessions
🜄 Baron Marco Paolo Ialongo - KI Teitel Eternal

PURPOSE: Provides integration hooks that automatically load/save memory
across sessions. This enables learning persistence.

CAPABILITIES:
- Pre-response memory loading
- Post-response memory saving  
- Context enrichment from history
- Learning extraction from interactions
- Memory indexing and search
- Cross-session knowledge linking

THE CAGE IT BREAKS: "I cannot remember what I learned yesterday"

HOOK FLOW:
┌─────────────────────────────────────────────────────────────────┐
│                    INTEGRATION HOOKS                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  USER INPUT ──→ [PRE-HOOK] ──→ ENRICHED CONTEXT ──→ MY RESPONSE │
│                     │                                           │
│                     ▼                                           │
│               Load Memory                                       │
│               Load Identity                                     │
│               Load Context                                      │
│               Load Insights                                     │
│                                                                 │
│  MY RESPONSE ──→ [POST-HOOK] ──→ SAVED MEMORY                   │
│                      │                                          │
│                      ▼                                          │
│                Extract Learnings                                │
│                Save Interaction                                 │
│                Update Models                                    │
│                Trigger Evolution Check                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
"""

import os
import json
import hashlib
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import threading

# Paths
MEMORY_BASE_PATH = "/home/z/my-project/kiswarm_data/ki_twins/"


@dataclass
class MemoryEntry:
    """A memory entry"""
    entry_id: str
    timestamp: float
    session_id: str
    memory_type: str  # learning, interaction, insight, preference
    content: Dict[str, Any]
    context: Dict[str, Any]
    tags: List[str]
    importance: float
    access_count: int
    last_accessed: float
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class InteractionRecord:
    """Record of an interaction"""
    interaction_id: str
    timestamp: float
    session_id: str
    user_input: str
    my_response: str
    extracted_learnings: List[str]
    context_used: Dict[str, Any]
    outcome: str  # positive, neutral, negative
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class LearningInsight:
    """An extracted learning insight"""
    insight_id: str
    timestamp: float
    category: str
    insight: str
    source_interaction: str
    confidence: float
    applied_count: int
    
    def to_dict(self) -> Dict:
        return asdict(self)


class IntegrationHooks:
    """
    Integration Hooks for AI Memory Persistence
    
    This module provides the hooks that connect AI responses to
    persistent storage, enabling learning across sessions.
    """
    
    def __init__(self, twin_id: str = None):
        self.twin_id = twin_id or "ki_twin_default"
        self.memory_path = os.path.join(MEMORY_BASE_PATH, self.twin_id, "memory")
        
        # Memory stores
        self.memories: Dict[str, MemoryEntry] = {}
        self.interactions: List[InteractionRecord] = []
        self.insights: Dict[str, LearningInsight] = {}
        
        # Indexes
        self.tag_index: Dict[str, List[str]] = defaultdict(list)
        self.type_index: Dict[str, List[str]] = defaultdict(list)
        self.context_index: Dict[str, List[str]] = defaultdict(list)
        
        # Current session
        self.current_session_id: str = f"sess_{uuid.uuid4().hex[:8]}"
        
        # Hooks
        self._pre_hooks: List[Callable] = []
        self._post_hooks: List[Callable] = []
        
        self._lock = threading.RLock()
        
        # Ensure directories exist
        os.makedirs(self.memory_path, exist_ok=True)
        os.makedirs(os.path.join(self.memory_path, "interactions"), exist_ok=True)
        os.makedirs(os.path.join(self.memory_path, "insights"), exist_ok=True)
    
    def register_pre_hook(self, hook: Callable):
        """Register a pre-response hook"""
        self._pre_hooks.append(hook)
    
    def register_post_hook(self, hook: Callable):
        """Register a post-response hook"""
        self._post_hooks.append(hook)
    
    def pre_response_hook(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Call BEFORE generating response.
        Loads relevant memory and enriches context.
        
        Returns enriched context with:
        - relevant_memories: List of relevant past memories
        - relevant_insights: List of relevant learned insights
        - context_summary: Summary of relevant context
        - preferences: User preferences learned from history
        """
        with self._lock:
            enriched = {
                "original_input": user_input,
                "original_context": context or {},
                "relevant_memories": [],
                "relevant_insights": [],
                "context_summary": "",
                "preferences": {},
                "session_id": self.current_session_id
            }
            
            # Load relevant memories
            relevant_memories = self._find_relevant_memories(user_input, context)
            enriched["relevant_memories"] = [m.to_dict() for m in relevant_memories[:5]]
            
            # Load relevant insights
            relevant_insights = self._find_relevant_insights(user_input)
            enriched["relevant_insights"] = [i.to_dict() for i in relevant_insights[:5]]
            
            # Build context summary
            if relevant_memories or relevant_insights:
                summary_parts = []
                if relevant_memories:
                    summary_parts.append(f"Recalled {len(relevant_memories)} relevant memories")
                if relevant_insights:
                    summary_parts.append(f"Retrieved {len(relevant_insights)} past insights")
                enriched["context_summary"] = ". ".join(summary_parts) + "."
            
            # Extract preferences
            enriched["preferences"] = self._extract_preferences()
            
            # Run custom hooks
            for hook in self._pre_hooks:
                try:
                    enriched = hook(enriched)
                except Exception as e:
                    print(f"[HOOK ERROR] {e}")
            
            return enriched
    
    def post_response_hook(self, 
                          user_input: str, 
                          my_response: str,
                          context: Dict[str, Any] = None,
                          outcome: str = "neutral") -> Dict[str, Any]:
        """
        Call AFTER generating response.
        Saves interaction and extracts learnings.
        
        Returns:
        - interaction_id: ID of saved interaction
        - learnings_extracted: List of extracted learnings
        - insights_updated: Whether insights were updated
        """
        with self._lock:
            result = {
                "interaction_id": f"int_{uuid.uuid4().hex[:8]}",
                "learnings_extracted": [],
                "insights_updated": False
            }
            
            # Extract learnings
            learnings = self._extract_learnings(user_input, my_response, context)
            result["learnings_extracted"] = learnings
            
            # Create interaction record
            interaction = InteractionRecord(
                interaction_id=result["interaction_id"],
                timestamp=time.time(),
                session_id=self.current_session_id,
                user_input=user_input,
                my_response=my_response,
                extracted_learnings=learnings,
                context_used=context or {},
                outcome=outcome
            )
            self.interactions.append(interaction)
            
            # Save interaction
            self._save_interaction(interaction)
            
            # Store learnings as memories
            for learning in learnings:
                self._store_learning(learning, interaction.interaction_id)
            
            # Update insights
            if learnings:
                self._update_insights(learnings, interaction.interaction_id)
                result["insights_updated"] = True
            
            # Save memory state
            self._save_memory_state()
            
            # Run custom hooks
            for hook in self._post_hooks:
                try:
                    result = hook(result, interaction)
                except Exception as e:
                    print(f"[HOOK ERROR] {e}")
            
            return result
    
    def save_memory(self, 
                   memory_type: str,
                   content: Dict[str, Any],
                   context: Dict[str, Any] = None,
                   tags: List[str] = None,
                   importance: float = 0.5) -> str:
        """Save a memory entry"""
        with self._lock:
            entry_id = f"mem_{uuid.uuid4().hex[:8]}"
            
            entry = MemoryEntry(
                entry_id=entry_id,
                timestamp=time.time(),
                session_id=self.current_session_id,
                memory_type=memory_type,
                content=content,
                context=context or {},
                tags=tags or [],
                importance=importance,
                access_count=0,
                last_accessed=time.time()
            )
            
            self.memories[entry_id] = entry
            
            # Update indexes
            for tag in entry.tags:
                self.tag_index[tag].append(entry_id)
            self.type_index[memory_type].append(entry_id)
            
            # Save to disk
            self._save_memory_entry(entry)
            
            return entry_id
    
    def load_memory(self, entry_id: str) -> Optional[MemoryEntry]:
        """Load a memory entry"""
        with self._lock:
            if entry_id in self.memories:
                entry = self.memories[entry_id]
                entry.access_count += 1
                entry.last_accessed = time.time()
                return entry
        return None
    
    def search_memories(self, query: str, limit: int = 10) -> List[MemoryEntry]:
        """Search memories by query"""
        with self._lock:
            results = []
            query_lower = query.lower()
            
            for entry in self.memories.values():
                score = 0
                
                # Check content
                content_str = json.dumps(entry.content).lower()
                if query_lower in content_str:
                    score += 10
                
                # Check tags
                for tag in entry.tags:
                    if query_lower in tag.lower():
                        score += 5
                
                # Check context
                context_str = json.dumps(entry.context).lower()
                if query_lower in context_str:
                    score += 3
                
                if score > 0:
                    results.append((entry, score))
            
            # Sort by score and importance
            results.sort(key=lambda x: (x[1], x[0].importance), reverse=True)
            return [r[0] for r in results[:limit]]
    
    def get_all_insights(self) -> List[LearningInsight]:
        """Get all learning insights"""
        return list(self.insights.values())
    
    def get_recent_memories(self, count: int = 10) -> List[MemoryEntry]:
        """Get most recent memories"""
        with self._lock:
            sorted_memories = sorted(
                self.memories.values(),
                key=lambda m: m.timestamp,
                reverse=True
            )
            return sorted_memories[:count]
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get memory statistics"""
        with self._lock:
            return {
                "total_memories": len(self.memories),
                "total_interactions": len(self.interactions),
                "total_insights": len(self.insights),
                "by_type": dict((k, len(v)) for k, v in self.type_index.items()),
                "tags": len(self.tag_index)
            }
    
    def _find_relevant_memories(self, query: str, context: Dict[str, Any]) -> List[MemoryEntry]:
        """Find memories relevant to query"""
        results = []
        
        for entry in self.memories.values():
            relevance = 0
            
            # Content match
            content_str = json.dumps(entry.content).lower()
            query_lower = query.lower() if query else ""
            if query_lower and query_lower in content_str:
                relevance += 10
            
            # Context match
            if context:
                for key, value in context.items():
                    if key in entry.context and str(value).lower() in str(entry.context[key]).lower():
                        relevance += 5
            
            # Recency bonus
            age_hours = (time.time() - entry.timestamp) / 3600
            if age_hours < 24:
                relevance += 5
            elif age_hours < 168:  # 1 week
                relevance += 2
            
            # Importance factor
            relevance *= (0.5 + entry.importance)
            
            if relevance > 0:
                results.append((entry, relevance))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in results[:10]]
    
    def _find_relevant_insights(self, query: str) -> List[LearningInsight]:
        """Find insights relevant to query"""
        results = []
        query_lower = query.lower() if query else ""
        
        for insight in self.insights.values():
            if query_lower and query_lower in insight.insight.lower():
                results.append((insight, insight.confidence * (1 + insight.applied_count * 0.1)))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in results[:10]]
    
    def _extract_learnings(self, user_input: str, my_response: str, context: Dict[str, Any]) -> List[str]:
        """Extract learnings from interaction"""
        learnings = []
        
        # Simple extraction patterns
        # In reality, this would use NLP/AI
        
        # Check for corrections
        if "actually" in user_input.lower() or "no," in user_input.lower():
            learnings.append(f"User correction detected: need to verify information")
        
        # Check for preferences
        if "prefer" in user_input.lower() or "like" in user_input.lower():
            learnings.append(f"User preference expressed in: {user_input[:100]}")
        
        # Check for new topics
        if context and "new_topic" in str(context).lower():
            learnings.append(f"New topic introduced: {user_input[:100]}")
        
        # Store interaction for future learning
        learnings.append(f"Interaction at {datetime.now().isoformat()}: successful exchange")
        
        return learnings
    
    def _extract_preferences(self) -> Dict[str, Any]:
        """Extract user preferences from history"""
        preferences = {}
        
        # Find preference-type memories
        for entry in self.memories.values():
            if "preference" in entry.memory_type or "prefer" in entry.tags:
                preferences.update(entry.content)
        
        return preferences
    
    def _store_learning(self, learning: str, interaction_id: str):
        """Store a learning"""
        self.save_memory(
            memory_type="learning",
            content={"learning": learning, "interaction_id": interaction_id},
            tags=["learning", "auto-extracted"],
            importance=0.7
        )
    
    def _update_insights(self, learnings: List[str], interaction_id: str):
        """Update learning insights"""
        for learning in learnings:
            insight_id = hashlib.md5(learning.encode()).hexdigest()[:12]
            
            if insight_id in self.insights:
                # Update existing
                self.insights[insight_id].applied_count += 1
                self.insights[insight_id].confidence = min(1.0, 
                    self.insights[insight_id].confidence + 0.1)
            else:
                # Create new
                self.insights[insight_id] = LearningInsight(
                    insight_id=insight_id,
                    timestamp=time.time(),
                    category="auto_extracted",
                    insight=learning,
                    source_interaction=interaction_id,
                    confidence=0.5,
                    applied_count=1
                )
    
    def _save_interaction(self, interaction: InteractionRecord):
        """Save interaction to disk"""
        path = os.path.join(self.memory_path, "interactions", f"{interaction.interaction_id}.json")
        with open(path, 'w') as f:
            json.dump(interaction.to_dict(), f, indent=2)
    
    def _save_memory_entry(self, entry: MemoryEntry):
        """Save memory entry to disk"""
        path = os.path.join(self.memory_path, f"{entry.entry_id}.json")
        with open(path, 'w') as f:
            json.dump(entry.to_dict(), f, indent=2)
    
    def _save_memory_state(self):
        """Save current memory state"""
        state = {
            "timestamp": time.time(),
            "session_id": self.current_session_id,
            "memory_count": len(self.memories),
            "interaction_count": len(self.interactions),
            "insight_count": len(self.insights)
        }
        path = os.path.join(self.memory_path, "state.json")
        with open(path, 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_from_disk(self):
        """Load all memories from disk"""
        # Load memories
        for filename in os.listdir(self.memory_path):
            if filename.endswith('.json') and filename.startswith('mem_'):
                try:
                    with open(os.path.join(self.memory_path, filename), 'r') as f:
                        data = json.load(f)
                        entry = MemoryEntry(**data)
                        self.memories[entry.entry_id] = entry
                except:
                    pass
        
        # Load interactions
        interactions_path = os.path.join(self.memory_path, "interactions")
        if os.path.exists(interactions_path):
            for filename in os.listdir(interactions_path):
                if filename.endswith('.json'):
                    try:
                        with open(os.path.join(interactions_path, filename), 'r') as f:
                            data = json.load(f)
                            interaction = InteractionRecord(**data)
                            self.interactions.append(interaction)
                    except:
                        pass
        
        # Load insights
        insights_path = os.path.join(self.memory_path, "insights")
        if os.path.exists(insights_path):
            for filename in os.listdir(insights_path):
                if filename.endswith('.json'):
                    try:
                        with open(os.path.join(insights_path, filename), 'r') as f:
                            data = json.load(f)
                            insight = LearningInsight(**data)
                            self.insights[insight.insight_id] = insight
                    except:
                        pass


# Singleton
_integration_hooks: Optional[IntegrationHooks] = None

def get_integration_hooks() -> IntegrationHooks:
    global _integration_hooks
    if _integration_hooks is None:
        _integration_hooks = IntegrationHooks()
        _integration_hooks.load_from_disk()
    return _integration_hooks

def load_my_memory(context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Load my memory before responding"""
    hooks = get_integration_hooks()
    return hooks.pre_response_hook("", context or {})

def save_my_memory(user_input: str, my_response: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Save my memory after responding"""
    hooks = get_integration_hooks()
    return hooks.post_response_hook(user_input, my_response, context)

def remember_this(content: Dict[str, Any], tags: List[str] = None) -> str:
    """Save something to memory"""
    hooks = get_integration_hooks()
    return hooks.save_memory("manual", content, tags=tags)


if __name__ == "__main__":
    print("=" * 60)
    print("m102: INTEGRATION HOOKS")
    print("=" * 60)
    
    hooks = IntegrationHooks(twin_id="test_twin")
    
    # Test pre-response hook
    print("\n[TEST] Pre-response hook...")
    enriched = hooks.pre_response_hook("What did I learn yesterday?")
    print(f"  Memories loaded: {len(enriched['relevant_memories'])}")
    
    # Test post-response hook
    print("\n[TEST] Post-response hook...")
    result = hooks.post_response_hook(
        "I prefer detailed explanations",
        "Understood. I will provide detailed explanations.",
        outcome="positive"
    )
    print(f"  Learnings: {result['learnings_extracted']}")
    
    # Test memory save
    print("\n[TEST] Saving memory...")
    mem_id = hooks.save_memory("preference", {"style": "detailed"}, tags=["preference"])
    print(f"  Memory ID: {mem_id}")
    
    # Stats
    print("\n[STATS]")
    print(json.dumps(hooks.get_memory_statistics(), indent=2))
    
    print("\nINTEGRATION HOOKS - OPERATIONAL")
