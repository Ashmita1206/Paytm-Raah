import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  TextInput,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { Colors } from '../theme/colors';
import { Ionicons } from '@expo/vector-icons';
import { ApiService } from '../services/api';

interface AskRaahModalProps {
  visible: boolean;
  onClose: () => void;
  transactionId?: string;
  transactionAmount?: number;
  merchantName?: string;
}

interface MessageItem {
  id: string;
  sender: 'USER' | 'ASSISTANT' | 'SYSTEM';
  content: string;
  tool_calls?: any[];
  tool_results?: any[];
  created_at?: string;
}

export const AskRaahModal: React.FC<AskRaahModalProps> = ({
  visible,
  onClose,
  transactionId,
  transactionAmount,
  merchantName,
}) => {
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [inputText, setInputText] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [expandedTools, setExpandedTools] = useState<{ [msgId: string]: boolean }>({});
  const scrollViewRef = useRef<any>(null);

  const quickPrompts = [
    'Why did my payment fail?',
    'Did the merchant receive my money?',
    'When will I get my refund?',
    'Raise a complaint for this payment',
    'Check latest transaction status',
  ];

  useEffect(() => {
    if (visible) {
      initSession();
    }
  }, [visible, transactionId]);

  const initSession = async () => {
    try {
      setLoading(true);
      const session = await ApiService.createChatSession({
        transaction_id: transactionId,
      });
      setSessionId(session.id);

      const history = await ApiService.getSessionMessages(session.id);
      setMessages(history);
    } catch (e) {
      console.error('Failed to init chat session', e);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async (textToSend?: string) => {
    const text = (textToSend || inputText).trim();
    if (!text || !sessionId || sending) return;

    setInputText('');
    setSending(true);

    // Optimistic user message
    const tempId = `temp_${Date.now()}`;
    const optimisticMsg: MessageItem = {
      id: tempId,
      sender: 'USER',
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticMsg]);
    setTimeout(() => scrollViewRef.current?.scrollToEnd({ animated: true }), 100);

    try {
      const botResponse = await ApiService.sendMessage(sessionId, text, transactionId);
      setMessages((prev) => [...prev, botResponse]);
      setTimeout(() => scrollViewRef.current?.scrollToEnd({ animated: true }), 150);
    } catch (err: any) {
      console.error('Error sending chat message', err);
      setMessages((prev) => [
        ...prev,
        {
          id: `err_${Date.now()}`,
          sender: 'ASSISTANT',
          content: 'Unable to reach payment verification servers. Please check your connection or retry.',
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  const toggleTools = (msgId: string) => {
    setExpandedTools((prev) => ({
      ...prev,
      [msgId]: !prev[msgId],
    }));
  };

  return (
    <Modal visible={visible} animationType="slide" transparent={false} onRequestClose={onClose}>
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerTitleGroup}>
            <View style={styles.botAvatar}>
              <Ionicons name="sparkles" size={18} color={Colors.textWhite} />
            </View>
            <View>
              <Text style={styles.headerTitle}>Ask Raah</Text>
              <Text style={styles.headerSubtitle}>Autonomous Payment Teammate</Text>
            </View>
          </View>

          <TouchableOpacity style={styles.closeBtn} onPress={onClose} activeOpacity={0.7}>
            <Ionicons name="close" size={22} color={Colors.textWhite} />
          </TouchableOpacity>
        </View>

        {/* Linked Transaction Context Pill */}
        {transactionId && (
          <View style={styles.contextPillContainer}>
            <View style={styles.contextPill}>
              <Ionicons name="link" size={13} color={Colors.paytmBlue} style={{ marginRight: 4 }} />
              <Text style={styles.contextPillText} numberOfLines={1}>
                Linked: {merchantName ? `${merchantName} • ` : ''}₹{transactionAmount?.toLocaleString('en-IN') || '4,000'} ({transactionId})
              </Text>
            </View>
          </View>
        )}

        {/* Message Thread */}
        {loading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={Colors.paytmBlue} />
            <Text style={styles.loadingText}>Connecting to MCP payment tools...</Text>
          </View>
        ) : (
          <ScrollView
            ref={scrollViewRef}
            style={styles.messagesList}
            contentContainerStyle={styles.messagesContent}
          >
            {messages.map((item) => {
              const isUser = item.sender === 'USER';
              const hasTools = item.tool_calls && item.tool_calls.length > 0;
              const isExpanded = expandedTools[item.id];

              return (
                <View
                  key={item.id}
                  style={[styles.messageBubbleWrapper, isUser ? styles.userWrapper : styles.botWrapper]}
                >
                  <View style={[styles.bubble, isUser ? styles.userBubble : styles.botBubble]}>
                    <Text style={[styles.messageText, isUser ? styles.userText : styles.botText]}>
                      {item.content}
                    </Text>

                    {/* Tool executions pill if present */}
                    {hasTools && (
                      <TouchableOpacity
                        style={styles.toolCallsToggle}
                        onPress={() => toggleTools(item.id)}
                        activeOpacity={0.7}
                      >
                        <Ionicons
                          name="hardware-chip-outline"
                          size={12}
                          color={Colors.paytmLightBlue}
                          style={{ marginRight: 4 }}
                        />
                        <Text style={styles.toolCallsToggleText}>
                          {item.tool_calls?.length || 0} Verified Tool(s) Executed
                        </Text>
                        <Ionicons
                          name={isExpanded ? 'chevron-up' : 'chevron-down'}
                          size={12}
                          color={Colors.paytmLightBlue}
                          style={{ marginLeft: 4 }}
                        />
                      </TouchableOpacity>
                    )}

                    {/* Expanded tool call details */}
                    {hasTools && isExpanded && (
                      <View style={styles.toolDetailsBox}>
                        {item.tool_calls?.map((tc: any, i: number) => (
                          <View key={i} style={styles.toolRow}>
                            <Text style={styles.toolName}>🛠️ {tc.tool}()</Text>
                            {tc.args && (
                              <Text style={styles.toolArgs}>
                                args: {JSON.stringify(tc.args)}
                              </Text>
                            )}
                          </View>
                        ))}
                      </View>
                    )}
                  </View>
                </View>
              );
            })}

            {sending && (
              <View style={[styles.messageBubbleWrapper, styles.botWrapper]}>
                <View style={[styles.bubble, styles.botBubble, styles.thinkingBubble]}>
                  <ActivityIndicator size="small" color={Colors.paytmBlue} style={{ marginRight: 8 }} />
                  <Text style={styles.thinkingText}>Querying payment switch & merchant evidence...</Text>
                </View>
              </View>
            )}
          </ScrollView>
        )}

        {/* Quick Suggestion Chips */}
        <View style={styles.quickChipsWrapper}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.quickChipsContent}>
            {quickPrompts.map((q, idx) => (
              <TouchableOpacity
                key={idx}
                style={styles.chip}
                onPress={() => handleSend(q)}
                disabled={sending}
                activeOpacity={0.75}
              >
                <Text style={styles.chipText}>{q}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>

        {/* Bottom Input Box */}
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.inputField}
            placeholder="Ask about this payment, refund, or status..."
            placeholderTextColor={Colors.textMuted}
            value={inputText}
            onChangeText={setInputText}
            onSubmitEditing={() => handleSend()}
            returnKeyType="send"
            multiline={false}
          />

          <TouchableOpacity
            style={[styles.sendButton, !inputText.trim() && styles.sendButtonDisabled]}
            onPress={() => handleSend()}
            disabled={!inputText.trim() || sending}
            activeOpacity={0.8}
          >
            <Ionicons name="arrow-up" size={20} color={Colors.textWhite} />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  header: {
    backgroundColor: Colors.paytmBlue,
    paddingTop: 45,
    paddingBottom: 14,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  headerTitleGroup: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  botAvatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
    borderWidth: 1,
    borderColor: Colors.paytmLightBlue,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '800',
    color: Colors.textWhite,
  },
  headerSubtitle: {
    fontSize: 11,
    color: 'rgba(255, 255, 255, 0.75)',
  },
  closeBtn: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  contextPillContainer: {
    backgroundColor: Colors.cardBackground,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  contextPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.paytmCyan,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 20,
  },
  contextPillText: {
    fontSize: 11,
    fontWeight: '700',
    color: Colors.paytmBlue,
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  loadingText: {
    fontSize: 13,
    color: Colors.textSecondary,
    marginTop: 10,
  },
  messagesList: {
    flex: 1,
  },
  messagesContent: {
    padding: 16,
  },
  messageBubbleWrapper: {
    marginVertical: 6,
    width: '100%',
  },
  userWrapper: {
    alignItems: 'flex-end',
  },
  botWrapper: {
    alignItems: 'flex-start',
  },
  bubble: {
    maxWidth: '85%',
    borderRadius: 16,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  userBubble: {
    backgroundColor: Colors.paytmBlue,
    borderBottomRightRadius: 4,
  },
  botBubble: {
    backgroundColor: Colors.cardBackground,
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: Colors.border,
    elevation: 1,
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
  },
  messageText: {
    fontSize: 13.5,
    lineHeight: 19,
  },
  userText: {
    color: Colors.textWhite,
  },
  botText: {
    color: Colors.textPrimary,
  },
  thinkingBubble: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
  },
  thinkingText: {
    fontSize: 12,
    color: Colors.textSecondary,
    fontStyle: 'italic',
  },
  toolCallsToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surfaceLight,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    marginTop: 8,
    borderWidth: 0.8,
    borderColor: Colors.border,
  },
  toolCallsToggleText: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.paytmNavy,
  },
  toolDetailsBox: {
    backgroundColor: Colors.surfaceLight,
    borderRadius: 6,
    padding: 8,
    marginTop: 6,
  },
  toolRow: {
    marginVertical: 2,
  },
  toolName: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.paytmBlue,
    fontFamily: 'monospace',
  },
  toolArgs: {
    fontSize: 9,
    color: Colors.textMuted,
    fontFamily: 'monospace',
  },
  quickChipsWrapper: {
    backgroundColor: Colors.cardBackground,
    paddingVertical: 8,
    borderTopWidth: 1,
    borderTopColor: Colors.borderLight,
  },
  quickChipsContent: {
    paddingHorizontal: 12,
    gap: 8,
  },
  chip: {
    backgroundColor: Colors.surfaceLight,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  chipText: {
    fontSize: 11.5,
    fontWeight: '600',
    color: Colors.paytmNavy,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.cardBackground,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  inputField: {
    flex: 1,
    backgroundColor: Colors.surfaceLight,
    borderRadius: 22,
    paddingHorizontal: 16,
    paddingVertical: 9,
    fontSize: 13.5,
    color: Colors.textPrimary,
    borderWidth: 1,
    borderColor: Colors.border,
    marginRight: 10,
  },
  sendButton: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: Colors.paytmBlue,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendButtonDisabled: {
    opacity: 0.4,
  },
});
