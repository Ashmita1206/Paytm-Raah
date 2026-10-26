import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Colors } from '../theme/colors';
import { Ionicons } from '@expo/vector-icons';
import { ApiService } from '../services/api';

interface ScenarioDrawerProps {
  visible: boolean;
  onClose: () => void;
  onScenarioTriggered?: (scenarioId: string, result: any) => void;
  onResetComplete?: () => void;
}

export const ScenarioDrawer: React.FC<ScenarioDrawerProps> = ({
  visible,
  onClose,
  onScenarioTriggered,
  onResetComplete,
}) => {
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [triggeringId, setTriggeringId] = useState<string | null>(null);

  useEffect(() => {
    if (visible) {
      loadScenarios();
    }
  }, [visible]);

  const loadScenarios = async () => {
    try {
      setLoading(true);
      const list = await ApiService.listScenarios();
      setScenarios(list);
    } catch (err) {
      console.error('Failed to load demo scenarios', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTrigger = async (scenId: string) => {
    try {
      setTriggeringId(scenId);
      const res = await ApiService.triggerScenario(scenId, 4000.0);
      if (onScenarioTriggered) {
        onScenarioTriggered(scenId, res);
      }
      onClose();
    } catch (err: any) {
      Alert.alert('Scenario Error', err.response?.data?.detail || err.message);
    } finally {
      setTriggeringId(null);
    }
  };

  const handleReset = async () => {
    try {
      setLoading(true);
      await ApiService.resetDemo();
      Alert.alert('Reset Success', 'Database reset and standard demo data re-seeded.');
      if (onResetComplete) {
        onResetComplete();
      }
      onClose();
    } catch (err: any) {
      Alert.alert('Reset Error', err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View style={styles.sheetContainer}>
          {/* Header */}
          <View style={styles.header}>
            <View style={styles.headerTitleRow}>
              <Ionicons name="flask-outline" size={20} color={Colors.paytmLightBlue} style={{ marginRight: 8 }} />
              <Text style={styles.headerTitle}>Demo Scenario Control Center</Text>
            </View>
            <TouchableOpacity style={styles.closeBtn} onPress={onClose} activeOpacity={0.7}>
              <Ionicons name="close" size={20} color={Colors.textPrimary} />
            </TouchableOpacity>
          </View>

          <Text style={styles.headerSubtitle}>
            Trigger synthetic payment failure and recovery events to test autonomous teammates in real-time.
          </Text>

          {/* Quick Database Reset & Seed Controls */}
          <View style={styles.quickActionRow}>
            <TouchableOpacity style={styles.resetBtn} onPress={handleReset} activeOpacity={0.8}>
              <Ionicons name="refresh" size={14} color={Colors.errorRed} style={{ marginRight: 4 }} />
              <Text style={styles.resetBtnText}>Reset & Seed Standard Demo Data</Text>
            </TouchableOpacity>
          </View>

          {loading ? (
            <View style={styles.loadingBox}>
              <ActivityIndicator size="large" color={Colors.paytmBlue} />
            </View>
          ) : (
            <ScrollView style={styles.scenarioList} contentContainerStyle={styles.scenarioListContent}>
              {scenarios.map((s) => {
                const isTriggering = triggeringId === s.id;
                return (
                  <TouchableOpacity
                    key={s.id}
                    style={styles.scenarioCard}
                    onPress={() => handleTrigger(s.id)}
                    disabled={isTriggering}
                    activeOpacity={0.85}
                  >
                    <View style={styles.scenarioCardHeader}>
                      <View style={styles.scenarioNumBadge}>
                        <Text style={styles.scenarioNumText}>Scenario {s.scenario_number}</Text>
                      </View>
                      <View style={styles.categoryBadge}>
                        <Text style={styles.categoryBadgeText}>{s.category}</Text>
                      </View>
                    </View>

                    <Text style={styles.scenarioName}>{s.name}</Text>
                    <Text style={styles.scenarioDesc}>{s.description}</Text>

                    <View style={styles.triggerRow}>
                      <Text style={styles.triggerActionLabel}>
                        {isTriggering ? 'Executing Agent Workflow...' : 'Tap to Trigger Live'}
                      </Text>
                      <Ionicons
                        name={isTriggering ? 'hourglass' : 'play-circle'}
                        size={18}
                        color={Colors.paytmLightBlue}
                      />
                    </View>
                  </TouchableOpacity>
                );
              })}
            </ScrollView>
          )}
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    justifyContent: 'flex-end',
  },
  sheetContainer: {
    backgroundColor: Colors.cardBackground,
    borderTopLeftRadius: 22,
    borderTopRightRadius: 22,
    maxHeight: '85%',
    paddingTop: 16,
    paddingBottom: 24,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    marginBottom: 4,
  },
  headerTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: Colors.paytmDeepBlue,
  },
  closeBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: Colors.surfaceLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerSubtitle: {
    fontSize: 11.5,
    color: Colors.textSecondary,
    paddingHorizontal: 20,
    marginBottom: 12,
    lineHeight: 16,
  },
  quickActionRow: {
    paddingHorizontal: 20,
    marginBottom: 12,
  },
  resetBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.errorLight,
    paddingVertical: 9,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(229, 57, 53, 0.2)',
  },
  resetBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: Colors.errorRed,
  },
  loadingBox: {
    padding: 30,
    alignItems: 'center',
  },
  scenarioList: {
    paddingHorizontal: 20,
  },
  scenarioListContent: {
    paddingBottom: 20,
  },
  scenarioCard: {
    backgroundColor: Colors.surfaceLight,
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  scenarioCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  scenarioNumBadge: {
    backgroundColor: Colors.paytmCyan,
    paddingHorizontal: 7,
    paddingVertical: 2,
    borderRadius: 5,
  },
  scenarioNumText: {
    fontSize: 10,
    fontWeight: '800',
    color: Colors.paytmBlue,
  },
  categoryBadge: {
    backgroundColor: Colors.borderLight,
    paddingHorizontal: 7,
    paddingVertical: 2,
    borderRadius: 5,
  },
  categoryBadgeText: {
    fontSize: 9,
    fontWeight: '700',
    color: Colors.textSecondary,
  },
  scenarioName: {
    fontSize: 13.5,
    fontWeight: '700',
    color: Colors.textPrimary,
    marginBottom: 4,
  },
  scenarioDesc: {
    fontSize: 11,
    color: Colors.textSecondary,
    lineHeight: 15,
    marginBottom: 8,
  },
  triggerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: Colors.borderLight,
    paddingTop: 6,
  },
  triggerActionLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: Colors.paytmBlue,
  },
});
