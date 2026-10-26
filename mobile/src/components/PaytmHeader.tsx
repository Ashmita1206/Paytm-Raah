import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { Colors } from '../theme/colors';
import { Ionicons } from '@expo/vector-icons';

interface PaytmHeaderProps {
  onOpenDemoMenu?: () => void;
  isOpsMode?: boolean;
  onToggleRole?: () => void;
  title?: string;
  subtitle?: string;
}

export const PaytmHeader: React.FC<PaytmHeaderProps> = ({
  onOpenDemoMenu,
  isOpsMode = false,
  onToggleRole,
  title = 'RAAH',
  subtitle = 'Autonomous Payment Intelligence',
}) => {
  return (
    <View style={styles.headerContainer}>
      <StatusBar style="light" />
      
      <View style={styles.topRow}>
        {/* User profile avatar & App Branding */}
        <View style={styles.brandingGroup}>
          <View style={styles.avatarCircle}>
            <Text style={styles.avatarText}>RS</Text>
          </View>
          <View style={styles.titleColumn}>
            <View style={styles.brandRow}>
              <Text style={styles.appName}>{title}</Text>
              <View style={styles.demoBadge}>
                <Text style={styles.demoBadgeText}>DEMO</Text>
              </View>
            </View>
            <Text style={styles.subtitleText}>{subtitle}</Text>
          </View>
        </View>

        {/* Right action controls: Role switcher & Demo scenarios menu */}
        <View style={styles.actionGroup}>
          {onToggleRole && (
            <TouchableOpacity
              style={[styles.roleButton, isOpsMode ? styles.roleButtonOps : styles.roleButtonCust]}
              onPress={onToggleRole}
              activeOpacity={0.8}
            >
              <Ionicons
                name={isOpsMode ? 'shield-checkmark' : 'person'}
                size={14}
                color={Colors.textWhite}
                style={{ marginRight: 4 }}
              />
              <Text style={styles.roleButtonText}>{isOpsMode ? 'Ops View' : 'Customer'}</Text>
            </TouchableOpacity>
          )}

          {onOpenDemoMenu && (
            <TouchableOpacity
              style={styles.demoControlBtn}
              onPress={onOpenDemoMenu}
              activeOpacity={0.8}
            >
              <Ionicons name="flask-outline" size={18} color={Colors.paytmLightBlue} />
            </TouchableOpacity>
          )}
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  headerContainer: {
    backgroundColor: Colors.paytmBlue,
    paddingTop: 45,
    paddingBottom: 16,
    paddingHorizontal: 16,
    borderBottomLeftRadius: 16,
    borderBottomRightRadius: 16,
    elevation: 4,
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  brandingGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  avatarCircle: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: Colors.paytmLightBlue,
    marginRight: 10,
  },
  avatarText: {
    color: Colors.textWhite,
    fontWeight: '700',
    fontSize: 14,
  },
  titleColumn: {
    justifyContent: 'center',
  },
  brandRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  appName: {
    color: Colors.textWhite,
    fontSize: 20,
    fontWeight: '800',
    letterSpacing: 0.8,
  },
  demoBadge: {
    backgroundColor: 'rgba(0, 186, 242, 0.25)',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
    marginLeft: 6,
    borderWidth: 0.8,
    borderColor: Colors.paytmLightBlue,
  },
  demoBadgeText: {
    color: Colors.paytmLightBlue,
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  subtitleText: {
    color: 'rgba(255, 255, 255, 0.75)',
    fontSize: 11,
    marginTop: 1,
  },
  actionGroup: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  roleButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 20,
    marginRight: 8,
  },
  roleButtonCust: {
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
  },
  roleButtonOps: {
    backgroundColor: Colors.accentPurple,
  },
  roleButtonText: {
    color: Colors.textWhite,
    fontSize: 11,
    fontWeight: '600',
  },
  demoControlBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    alignItems: 'center',
    justifyContent: 'center',
  },
});
