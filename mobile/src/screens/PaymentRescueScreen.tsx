import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Colors } from '../theme/colors';
import { Ionicons } from '@expo/vector-icons';
import { ApiService } from '../services/api';
import { RescueCard } from '../components/RescueCard';
import { TimelineMoney } from '../components/TimelineMoney';
import { TimelineRescue } from '../components/TimelineRescue';
import { FloatingAskRaah } from '../components/FloatingAskRaah';
import { AskRaahModal } from '../components/AskRaahModal';

interface PaymentRescueScreenProps {
  route: any;
  navigation: any;
}

export const PaymentRescueScreen: React.FC<PaymentRescueScreenProps> = ({
  route,
  navigation,
}) => {
  const transactionId = route.params?.transactionId || 'tx_demo_4000_grocery';
  const [journeyData, setJourneyData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [checking, setChecking] = useState(false);
  const [showAskRaah, setShowAskRaah] = useState(false);

  const loadJourney = useCallback(async () => {
    try {
      const data = await ApiService.getPaymentJourney(transactionId);
      setJourneyData(data);
    } catch (err: any) {
      console.error('Failed to load payment journey', err);
      Alert.alert('Load Error', 'Unable to retrieve payment journey from resolution server.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [transactionId]);

  useEffect(() => {
    loadJourney();
    const interval = setInterval(() => {
      // Background poll for updates every 8 seconds while screen is open
      loadJourney();
    }, 8000);
    return () => clearInterval(interval);
  }, [loadJourney]);

  const onRefresh = () => {
    setRefreshing(true);
    loadJourney();
  };

  const handleManualRecheck = async () => {
    if (!journeyData?.rescue_card?.case_number) return;
    try {
      setChecking(true);
      await ApiService.triggerCaseFollowup(journeyData.rescue_card.case_number);
      await loadJourney();
      Alert.alert('Autonomous Check Complete', 'Queried payment switch and updated Timeline B with latest verified records.');
    } catch (e: any) {
      Alert.alert('Recheck Failed', e.message);
    } finally {
      setChecking(false);
    }
  };

  const handleSimulateReversal = async () => {
    try {
      setChecking(true);
      await ApiService.triggerScenario('5', journeyData?.amount || 4000.0);
      await loadJourney();
      Alert.alert('Simulated Reversal Credited', 'Payer bank acknowledged refund credit. Timelines updated to RESOLVED.');
    } catch (e: any) {
      Alert.alert('Simulation Error', e.message);
    } finally {
      setChecking(false);
    }
  };

  if (loading && !journeyData) {
    return (
      <View style={styles.loadingScreen}>
        <ActivityIndicator size="large" color={Colors.paytmBlue} />
        <Text style={styles.loadingScreenText}>Loading Raah Rescue Investigation...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Top Navigation Bar */}
      <View style={styles.navBar}>
        <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()} activeOpacity={0.7}>
          <Ionicons name="arrow-back" size={22} color={Colors.textWhite} />
        </TouchableOpacity>
        <View style={styles.navTitleCol}>
          <Text style={styles.navTitle}>Payment Rescue Tracker</Text>
          <Text style={styles.navSubtitle}>Autonomous Recovery & Dispute Engine</Text>
        </View>
        <TouchableOpacity style={styles.refreshBtn} onPress={onRefresh} activeOpacity={0.7}>
          <Ionicons name="reload" size={18} color={Colors.textWhite} />
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.scrollArea}
        contentContainerStyle={styles.scrollContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[Colors.paytmBlue]} />}
      >
        {/* Flagship Payment Rescue Information Card */}
        {journeyData?.rescue_card && (
          <RescueCard
            data={journeyData.rescue_card}
            onTriggerCheck={handleManualRecheck}
            checking={checking}
          />
        )}

        {/* Quick Demo Reversal Button for Hackathon Judges */}
        <View style={styles.demoControlBox}>
          <View style={styles.demoControlHeader}>
            <Ionicons name="flask-outline" size={14} color={Colors.paytmBlue} style={{ marginRight: 4 }} />
            <Text style={styles.demoControlTitle}>DEMO SIMULATION CONTROL</Text>
          </View>
          <TouchableOpacity
            style={styles.simulateRevBtn}
            onPress={handleSimulateReversal}
            disabled={checking}
            activeOpacity={0.85}
          >
            <Ionicons name="refresh-circle" size={18} color={Colors.textWhite} style={{ marginRight: 6 }} />
            <Text style={styles.simulateRevBtnText}>Simulate Bank Reversal Event (Scenario 5)</Text>
          </TouchableOpacity>
        </View>

        {/* TIMELINE A: MONEY JOURNEY (Evidence-backed states) */}
        <TimelineMoney events={journeyData?.money_journey || []} />

        {/* TIMELINE B: AI RESOLUTION JOURNEY (Autonomous agent actions & tool calls) */}
        <TimelineRescue actions={journeyData?.ai_resolution_journey || []} />

        {/* Action Button: Open Contextual Chat */}
        <View style={styles.bottomActionBox}>
          <TouchableOpacity
            style={styles.askRaahCaseBtn}
            onPress={() => setShowAskRaah(true)}
            activeOpacity={0.85}
          >
            <Ionicons name="chatbubble-ellipses" size={18} color={Colors.textWhite} style={{ marginRight: 8 }} />
            <Text style={styles.askRaahCaseBtnText}>Ask Raah About This Case</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>

      {/* Floating Ask Raah Button */}
      <FloatingAskRaah
        onPress={() => setShowAskRaah(true)}
        hasUnread={false}
      />

      {/* Contextual Chat Modal */}
      <AskRaahModal
        visible={showAskRaah}
        onClose={() => setShowAskRaah(false)}
        transactionId={transactionId}
        transactionAmount={journeyData?.amount}
        merchantName={journeyData?.merchant_name}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  loadingScreen: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.background,
  },
  loadingScreenText: {
    fontSize: 13,
    color: Colors.textSecondary,
    marginTop: 12,
    fontWeight: '600',
  },
  navBar: {
    backgroundColor: Colors.paytmBlue,
    paddingTop: 45,
    paddingBottom: 14,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    elevation: 4,
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
  },
  backBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  navTitleCol: {
    flex: 1,
    marginHorizontal: 12,
  },
  navTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: Colors.textWhite,
  },
  navSubtitle: {
    fontSize: 10.5,
    color: 'rgba(255, 255, 255, 0.75)',
  },
  refreshBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  scrollArea: {
    flex: 1,
  },
  scrollContent: {
    paddingVertical: 10,
    paddingBottom: 90,
  },
  demoControlBox: {
    backgroundColor: Colors.cardBackground,
    borderRadius: 14,
    marginHorizontal: 16,
    marginVertical: 4,
    padding: 12,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  demoControlHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  demoControlTitle: {
    fontSize: 10,
    fontWeight: '800',
    color: Colors.paytmBlue,
    letterSpacing: 0.6,
  },
  simulateRevBtn: {
    backgroundColor: Colors.paytmBlue,
    borderRadius: 10,
    paddingVertical: 10,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  simulateRevBtnText: {
    color: Colors.textWhite,
    fontSize: 12,
    fontWeight: '700',
  },
  bottomActionBox: {
    paddingHorizontal: 16,
    marginTop: 8,
    marginBottom: 16,
  },
  askRaahCaseBtn: {
    backgroundColor: Colors.paytmBlue,
    borderRadius: 14,
    paddingVertical: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  askRaahCaseBtnText: {
    color: Colors.textWhite,
    fontSize: 14,
    fontWeight: '800',
  },
});
