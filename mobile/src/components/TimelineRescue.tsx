import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors } from '../theme/colors';
import { Ionicons } from '@expo/vector-icons';

export interface AIActionItem {
  id: string;
  agent_type: string;
  tool_invoked: string;
  action_title: string;
  action_description?: string;
  validation_outcome: string;
  execution_outcome: string;
  created_at: string;
}

interface TimelineRescueProps {
  actions: AIActionItem[];
}

export const TimelineRescue: React.FC<TimelineRescueProps> = ({ actions }) => {
  const getToolIcon = (tool: string) => {
    switch (tool) {
      case 'investigation_started':
        return 'search';
      case 'get_transaction_status':
        return 'server-outline';
      case 'get_payment_events':
        return 'list-outline';
      case 'get_merchant_confirmation':
        return 'storefront-outline';
      case 'get_applicable_reversal_policy':
        return 'shield-checkmark-outline';
      case 'create_resolution_case':
        return 'folder-open-outline';
      case 'schedule_case_followup':
        return 'alarm-outline';
      case 'poll_reversal_switch':
        return 'sync-outline';
      case 'verify_bank_reversal':
        return 'ribbon-outline';
      case 'correlate_incident':
        return 'git-network-outline';
      case 'request_human_review':
        return 'people-outline';
      default:
        return 'hardware-chip-outline';
    }
  };

  const formatTimestamp = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return isoString;
    }
  };

  if (!actions || actions.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyText}>Autonomous resolution agent standby.</Text>
      </View>
    );
  }

  return (
    <View style={styles.timelineContainer}>
      <View style={styles.sectionHeader}>
        <View style={styles.headerIconCircle}>
          <Ionicons name="hardware-chip-outline" size={16} color={Colors.accentPurple} />
        </View>
        <Text style={styles.sectionTitle}>TIMELINE B: AI RESOLUTION JOURNEY</Text>
        <View style={styles.agentTypeBadge}>
          <Text style={styles.agentTypeText}>LangGraph + MCP</Text>
        </View>
      </View>

      <Text style={styles.timelineSubtitle}>
        Audited autonomous agent actions executed across MCP tool servers and regulatory policies.
      </Text>

      {actions.map((act, index) => {
        const isLast = index === actions.length - 1;
        const isIncident = act.tool_invoked === 'correlate_incident';

        return (
          <View key={act.id || index} style={styles.eventRow}>
            {/* Left timeline line & icon node */}
            <View style={styles.nodeColumn}>
              <View style={[styles.iconNode, isIncident ? styles.iconNodePurple : styles.iconNodeBlue]}>
                <Ionicons
                  name={getToolIcon(act.tool_invoked) as any}
                  size={14}
                  color={isIncident ? Colors.accentPurple : Colors.paytmBlue}
                />
              </View>
              {!isLast && <View style={styles.verticalLine} />}
            </View>

            {/* Right event content */}
            <View style={[styles.eventContent, isLast && styles.lastEventContent]}>
              <View style={styles.eventTitleRow}>
                <Text style={styles.eventTitle}>{act.action_title}</Text>
                <Text style={styles.timestampText}>{formatTimestamp(act.created_at)}</Text>
              </View>

              {act.action_description && (
                <Text style={styles.eventDescription}>{act.action_description}</Text>
              )}

              {/* Tool name & execution badge */}
              <View style={styles.badgeRow}>
                <View style={styles.toolBadge}>
                  <Text style={styles.toolBadgeText}>MCP: {act.tool_invoked}()</Text>
                </View>
                <View style={styles.agentBadge}>
                  <Text style={styles.agentBadgeText}>{act.agent_type}</Text>
                </View>
                <View style={styles.outcomeBadge}>
                  <Ionicons name="checkmark-sharp" size={10} color={Colors.successGreen} style={{ marginRight: 2 }} />
                  <Text style={styles.outcomeBadgeText}>{act.execution_outcome}</Text>
                </View>
              </View>
            </View>
          </View>
        );
      })}
    </View>
  );
};

const styles = StyleSheet.create({
  timelineContainer: {
    backgroundColor: Colors.cardBackground,
    borderRadius: 18,
    padding: 18,
    marginHorizontal: 16,
    marginVertical: 10,
    elevation: 3,
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 6,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  headerIconCircle: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: 'rgba(124, 58, 237, 0.1)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 8,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: Colors.paytmDeepBlue,
    letterSpacing: 0.6,
    flex: 1,
  },
  agentTypeBadge: {
    backgroundColor: 'rgba(124, 58, 237, 0.12)',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  agentTypeText: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.accentPurple,
  },
  timelineSubtitle: {
    fontSize: 11,
    color: Colors.textMuted,
    marginBottom: 16,
    lineHeight: 15,
  },
  eventRow: {
    flexDirection: 'row',
  },
  nodeColumn: {
    alignItems: 'center',
    width: 32,
    marginRight: 10,
  },
  iconNode: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: Colors.cardBackground,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.8,
    zIndex: 2,
  },
  iconNodeBlue: {
    borderColor: Colors.paytmLightBlue,
  },
  iconNodePurple: {
    borderColor: Colors.accentPurple,
  },
  verticalLine: {
    width: 2,
    flex: 1,
    backgroundColor: Colors.borderLight,
    marginVertical: 4,
  },
  eventContent: {
    flex: 1,
    paddingBottom: 20,
  },
  lastEventContent: {
    paddingBottom: 4,
  },
  eventTitleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  eventTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: Colors.textPrimary,
    flex: 1,
  },
  timestampText: {
    fontSize: 10,
    color: Colors.textMuted,
    fontWeight: '500',
  },
  eventDescription: {
    fontSize: 11.5,
    color: Colors.textSecondary,
    lineHeight: 16,
    marginTop: 3,
  },
  badgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 6,
    flexWrap: 'wrap',
    gap: 6,
  },
  toolBadge: {
    backgroundColor: Colors.paytmCyan,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  toolBadgeText: {
    fontSize: 9.5,
    fontWeight: '700',
    color: Colors.paytmBlue,
    fontFamily: 'monospace',
  },
  agentBadge: {
    backgroundColor: Colors.surfaceLight,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    borderWidth: 0.8,
    borderColor: Colors.border,
  },
  agentBadgeText: {
    fontSize: 9,
    fontWeight: '600',
    color: Colors.textSecondary,
  },
  outcomeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.successLight,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  outcomeBadgeText: {
    fontSize: 9,
    fontWeight: '700',
    color: Colors.successGreen,
  },
  emptyContainer: {
    padding: 20,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 12,
    color: Colors.textMuted,
    fontStyle: 'italic',
  },
});
