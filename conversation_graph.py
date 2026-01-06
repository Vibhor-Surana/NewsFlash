import logging
from typing import Dict, List, Any, Literal, TypedDict
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import MessageGraph
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from config import Config
from language_service import LanguageService
import os

# Set environment variables for LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = Config.LANGSMITH_ENDPOINT
os.environ["LANGCHAIN_API_KEY"] = Config.LANGSMITH_API_KEY
os.environ["LANGCHAIN_PROJECT"] = Config.LANGSMITH_PROJECT

logger = logging.getLogger(__name__)

class ConversationState(TypedDict):
    topics: List[str]
    user_input: str
    stage: Literal["collecting", "searching", "completed", "language_selection"]
    response: str
    next_action: str
    language: str
    language_confirmed: bool

class NewsConversationGraph:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=Config.GEMINI_API_KEY,
            temperature=0.1
        )
        
        # Initialize language-specific prompts
        self._init_language_prompts()
        
        # Create the conversation graph
        self.graph = self._create_graph()
        logger.info("ConversationGraph initialized successfully")
    
    def _init_language_prompts(self):
        """Initialize language-specific conversation prompts"""
        self.language_prompts = {
            'en': {
                'welcome': "Hello! I'm your news assistant. What language would you prefer for news summaries? (English/Hindi/Marathi) or just say 'English' to continue.",
                'language_set': "Great! I'll provide news summaries in {language}. What topic would you like to search for news about?",
                'topic_added': "Added '{topic}' to your search topics. Do you want to search about anything else? (Enter another topic or say 'no' to search)",
                'topic_exists': "You've already added '{topic}'. Do you want to search about anything else? (Enter another topic or say 'no' to search)",
                'search_ready': "Great! I'll search for news on these topics: {topics}. Please wait while I gather the latest news...",
                'need_topic': "Please enter at least one topic to search for news.",
                'ask_topic': "Please enter a topic you'd like to search for news about."
            },
            'hi': {
                'welcome': "नमस्ते! मैं आपका समाचार सहायक हूं। आप समाचार सारांश किस भाषा में पसंद करेंगे? (English/Hindi/Marathi) या बस 'Hindi' कहें।",
                'language_set': "बहुत बढ़िया! मैं {language} में समाचार सारांश प्रदान करूंगा। आप किस विषय पर समाचार खोजना चाहते हैं?",
                'topic_added': "'{topic}' को आपके खोज विषयों में जोड़ दिया गया। क्या आप कुछ और खोजना चाहते हैं? (कोई और विषय दर्ज करें या खोजने के लिए 'no' कहें)",
                'topic_exists': "आपने पहले से ही '{topic}' जोड़ा है। क्या आप कुछ और खोजना चाहते हैं? (कोई और विषय दर्ज करें या खोजने के लिए 'no' कहें)",
                'search_ready': "बहुत बढ़िया! मैं इन विषयों पर समाचार खोजूंगा: {topics}। कृपया प्रतीक्षा करें जब तक मैं नवीनतम समाचार एकत्र करता हूं...",
                'need_topic': "कृपया समाचार खोजने के लिए कम से कम एक विषय दर्ज करें।",
                'ask_topic': "कृपया एक विषय दर्ज करें जिसके बारे में आप समाचार खोजना चाहते हैं।"
            },
            'mr': {
                'welcome': "नमस्कार! मी तुमचा बातमी सहाय्यक आहे। तुम्ही बातम्यांचा सारांश कोणत्या भाषेत पसंत कराल? (English/Hindi/Marathi) किंवा फक्त 'Marathi' म्हणा।",
                'language_set': "उत्तम! मी {language} मध्ये बातम्यांचा सारांश देईन। तुम्ही कोणत्या विषयावर बातम्या शोधू इच्छिता?",
                'topic_added': "'{topic}' तुमच्या शोध विषयांमध्ये जोडले गेले. तुम्ही आणखी काही शोधू इच्छिता? (दुसरा विषय टाका किंवा शोधण्यासाठी 'no' म्हणा)",
                'topic_exists': "तुम्ही आधीच '{topic}' जोडले आहे. तुम्ही आणखी काही शोधू इच्छिता? (दुसरा विषय टाका किंवा शोधण्यासाठी 'no' म्हणा)",
                'search_ready': "उत्तम! मी या विषयांवर बातम्या शोधेन: {topics}. कृपया प्रतीक्षा करा जेव्हा मी नवीनतम बातम्या गोळा करतो...",
                'need_topic': "कृपया बातम्या शोधण्यासाठी किमान एक विषय टाका.",
                'ask_topic': "कृपया एक विषय टाका ज्याबद्दल तुम्ही बातम्या शोधू इच्छिता."
            }
        }

    def _create_graph(self):
        """Create the conversation state graph using LangGraph"""
        
        def process_user_input(state: ConversationState) -> ConversationState:
            """Process user input and determine next action with language support"""
            user_input = state.get("user_input", "").strip()
            user_input_lower = user_input.lower()
            topics = state.get("topics", [])
            stage = state.get("stage", "language_selection")
            language = state.get("language", "en")
            language_confirmed = state.get("language_confirmed", False)
            
            logger.debug(f"Processing user input: {user_input}, current topics: {topics}, stage: {stage}, language: {language}")
            
            # Handle language selection stage
            if stage == "language_selection" or not language_confirmed:
                detected_language = self._detect_language_preference(user_input_lower)
                if detected_language:
                    prompts = self.language_prompts.get(detected_language, self.language_prompts['en'])
                    language_name = LanguageService.get_language_name(detected_language)
                    return {
                        "topics": topics,
                        "stage": "collecting",
                        "language": detected_language,
                        "language_confirmed": True,
                        "response": prompts['language_set'].format(language=language_name),
                        "next_action": "collect"
                    }
                else:
                    # If no language detected, ask again
                    return {
                        "topics": topics,
                        "stage": "language_selection",
                        "language": "en",
                        "language_confirmed": False,
                        "response": self.language_prompts['en']['welcome'],
                        "next_action": "select_language"
                    }
            
            # Get prompts for current language
            prompts = self.language_prompts.get(language, self.language_prompts['en'])
            
            # Handle topic collection stage
            if stage == "collecting":
                # Check if user wants to stop adding topics
                if user_input_lower in ["no", "n", "stop", "search", "done", "नहीं", "नाही"]:
                    if topics:
                        return {
                            "topics": topics,
                            "stage": "searching",
                            "language": language,
                            "language_confirmed": language_confirmed,
                            "response": prompts['search_ready'].format(topics=', '.join(topics)),
                            "next_action": "search"
                        }
                    else:
                        return {
                            "topics": topics,
                            "stage": "collecting",
                            "language": language,
                            "language_confirmed": language_confirmed,
                            "response": prompts['need_topic'],
                            "next_action": "collect"
                        }
                
                # If we have input, add it as a topic
                if user_input and user_input not in topics:
                    topics.append(user_input)
                    return {
                        "topics": topics,
                        "stage": "collecting",
                        "language": language,
                        "language_confirmed": language_confirmed,
                        "response": prompts['topic_added'].format(topic=user_input),
                        "next_action": "collect"
                    }
                elif user_input in topics:
                    return {
                        "topics": topics,
                        "stage": "collecting",
                        "language": language,
                        "language_confirmed": language_confirmed,
                        "response": prompts['topic_exists'].format(topic=user_input),
                        "next_action": "collect"
                    }
                else:
                    return {
                        "topics": topics,
                        "stage": "collecting",
                        "language": language,
                        "language_confirmed": language_confirmed,
                        "response": prompts['ask_topic'],
                        "next_action": "collect"
                    }
            
            # Default fallback
            return {
                "topics": topics,
                "stage": "collecting",
                "language": language,
                "language_confirmed": language_confirmed,
                "response": prompts['ask_topic'],
                "next_action": "collect"
            }

        def generate_response(state: ConversationState) -> ConversationState:
            """Generate conversational response with language support"""
            topics = state.get("topics", [])
            stage = state.get("stage", "language_selection")
            language = state.get("language", "en")
            language_confirmed = state.get("language_confirmed", False)
            
            # Get prompts for current language
            prompts = self.language_prompts.get(language, self.language_prompts['en'])
            
            if stage == "language_selection" or not language_confirmed:
                response = self.language_prompts['en']['welcome']
            elif stage == "collecting" and not topics:
                response = prompts['ask_topic']
            elif stage == "collecting" and topics:
                response = f"Current topics: {', '.join(topics)}. " + prompts['topic_added'].split('.')[1].strip()
            elif stage == "searching":
                response = prompts['search_ready'].format(topics=', '.join(topics))
            else:
                response = prompts['ask_topic']
            
            return {
                **state,
                "response": response
            }

        # Create state graph
        workflow = StateGraph(ConversationState)
        
        # Add nodes
        workflow.add_node("process_input", process_user_input)
        workflow.add_node("generate_response", generate_response)
        
        # Define edges
        workflow.set_entry_point("process_input")
        workflow.add_edge("process_input", END)
        
        return workflow.compile()
    
    def _detect_language_preference(self, user_input: str) -> str:
        """Detect language preference from user input"""
        user_input = user_input.lower().strip()
        
        # Direct language mentions - check Marathi first to avoid Hindi false positive
        if any(word in user_input for word in ['marathi', 'mr', 'मराठी']):
            return 'mr'
        elif any(word in user_input for word in ['hindi', 'hi', 'हिंदी', 'हिन्दी']):
            return 'hi'
        elif any(word in user_input for word in ['english', 'en']):
            return 'en'
        
        # Check for language-specific words/phrases - Marathi first
        marathi_indicators = ['नमस्कार', 'होय', 'नाही', 'काय', 'कसे', 'बातम्या', 'तुम्ही', 'मध्ये', 'च्या']
        hindi_indicators = ['नमस्ते', 'हाँ', 'हां', 'नहीं', 'क्या', 'कैसे', 'समाचार', 'आप', 'में', 'के']
        
        if any(word in user_input for word in marathi_indicators):
            return 'mr'
        elif any(word in user_input for word in hindi_indicators):
            return 'hi'
        
        # Default to None if no clear preference detected
        return None
    
    def get_language_from_state(self, state: Dict[str, Any]) -> str:
        """Get the current language from conversation state"""
        return state.get("language", LanguageService.get_default_language())
    
    def set_language_preference(self, state: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Set language preference in conversation state"""
        validated_language = LanguageService.get_fallback_language(language)
        state["language"] = validated_language
        state["language_confirmed"] = True
        logger.info(f"Language preference set to: {validated_language}")
        return state
    
    def is_language_confirmed(self, state: Dict[str, Any]) -> bool:
        """Check if language preference has been confirmed"""
        return state.get("language_confirmed", False)
    
    def reset_conversation_state(self, language: str = None) -> Dict[str, Any]:
        """Reset conversation state with optional language preference"""
        if language and LanguageService.validate_language(language):
            return {
                "topics": [],
                "stage": "collecting",
                "user_input": "",
                "response": "",
                "next_action": "collect",
                "language": language,
                "language_confirmed": True
            }
        else:
            return {
                "topics": [],
                "stage": "language_selection",
                "user_input": "",
                "response": "",
                "next_action": "select_language",
                "language": "en",
                "language_confirmed": False
            }

    def process_conversation(self, user_input: str, current_state: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a conversation turn with language support"""
        if current_state is None:
            current_state = {
                "topics": [],
                "stage": "language_selection",
                "user_input": user_input,
                "response": "",
                "next_action": "select_language",
                "language": "en",
                "language_confirmed": False
            }
        else:
            current_state["user_input"] = user_input

        try:
            # Use LangGraph for full conversation management
            result = self.graph.invoke(current_state)
            logger.info(f"Conversation processed successfully: {result}")
            return result
        except Exception as e:
            logger.error(f"Error processing conversation: {e}")
            language = current_state.get("language", "en")
            prompts = self.language_prompts.get(language, self.language_prompts['en'])
            return {
                "topics": current_state.get("topics", []),
                "stage": "collecting", 
                "language": language,
                "language_confirmed": current_state.get("language_confirmed", False),
                "response": "I apologize, but I encountered an error. Please try again." if language == "en" else prompts.get('ask_topic', "Please try again."),
                "next_action": "collect"
            }
    
    def _process_user_input_simple(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Simple conversation processing without AI with language support"""
        user_input = state.get("user_input", "").strip()
        user_input_lower = user_input.lower()
        topics = state.get("topics", [])
        stage = state.get("stage", "language_selection")
        language = state.get("language", "en")
        language_confirmed = state.get("language_confirmed", False)
        
        logger.debug(f"Processing user input: {user_input}, current topics: {topics}, stage: {stage}, language: {language}")
        
        # Handle language selection stage
        if stage == "language_selection" or not language_confirmed:
            detected_language = self._detect_language_preference(user_input_lower)
            if detected_language:
                prompts = self.language_prompts.get(detected_language, self.language_prompts['en'])
                language_name = LanguageService.get_language_name(detected_language)
                return {
                    "topics": topics,
                    "stage": "collecting",
                    "language": detected_language,
                    "language_confirmed": True,
                    "response": prompts['language_set'].format(language=language_name),
                    "next_action": "collect"
                }
            else:
                return {
                    "topics": topics,
                    "stage": "language_selection",
                    "language": "en",
                    "language_confirmed": False,
                    "response": self.language_prompts['en']['welcome'],
                    "next_action": "select_language"
                }
        
        # Get prompts for current language
        prompts = self.language_prompts.get(language, self.language_prompts['en'])
        
        # Handle topic collection stage
        if stage == "collecting":
            # Check if user wants to stop adding topics
            if user_input_lower in ["no", "n", "stop", "search", "done", "नहीं", "नाही"]:
                if topics:
                    return {
                        "topics": topics,
                        "stage": "searching",
                        "language": language,
                        "language_confirmed": language_confirmed,
                        "response": prompts['search_ready'].format(topics=', '.join(topics)),
                        "next_action": "search"
                    }
                else:
                    return {
                        "topics": topics,
                        "stage": "collecting",
                        "language": language,
                        "language_confirmed": language_confirmed,
                        "response": prompts['need_topic'],
                        "next_action": "collect"
                    }
            
            # If we have input, add it as a topic
            if user_input and user_input not in topics:
                topics.append(user_input)
                return {
                    "topics": topics,
                    "stage": "collecting",
                    "language": language,
                    "language_confirmed": language_confirmed,
                    "response": prompts['topic_added'].format(topic=user_input),
                    "next_action": "collect"
                }
            elif user_input in topics:
                return {
                    "topics": topics,
                    "stage": "collecting", 
                    "language": language,
                    "language_confirmed": language_confirmed,
                    "response": prompts['topic_exists'].format(topic=user_input),
                    "next_action": "collect"
                }
            else:
                return {
                    "topics": topics,
                    "stage": "collecting",
                    "language": language,
                    "language_confirmed": language_confirmed,
                    "response": prompts['ask_topic'],
                    "next_action": "collect"
                }
        
        # Default fallback
        return {
            "topics": topics,
            "stage": "collecting",
            "language": language,
            "language_confirmed": language_confirmed,
            "response": prompts['ask_topic'],
            "next_action": "collect"
        }

    def should_search_news(self, state: Dict[str, Any]) -> bool:
        """Check if we should proceed to search for news"""
        return state.get("stage") == "searching" and len(state.get("topics", [])) > 0
