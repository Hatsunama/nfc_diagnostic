from pathlib import Path
import os, subprocess
p=Path(__file__).parent
sdk=Path(os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT") or str(Path(os.environ["LOCALAPPDATA"])/"Android/Sdk"))
bt=sdk/'build-tools/36.0.0'
jar=sdk/'platforms/android-36/android.jar'
def run(*a): subprocess.run([str(x) for x in a],cwd=p,check=True)
(p/'src/lab/nfc').mkdir(parents=True,exist_ok=True)
(p/'res/xml').mkdir(parents=True,exist_ok=True)
(p/'classes').mkdir(exist_ok=True)
(p/'dex').mkdir(exist_ok=True)
(p/'AndroidManifest.xml').write_text('''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="lab.nfc"><uses-sdk android:minSdkVersion="23" android:targetSdkVersion="28"/><uses-permission android:name="android.permission.NFC"/><application android:theme="@android:style/Theme.Material.Light" android:label="NFC Diagnostic"><activity android:name=".Main" android:exported="true"><intent-filter><action android:name="android.intent.action.MAIN"/><category android:name="android.intent.category.LAUNCHER"/></intent-filter></activity><service android:name=".Card" android:exported="true" android:permission="android.permission.BIND_NFC_SERVICE"><intent-filter><action android:name="android.nfc.cardemulation.action.HOST_APDU_SERVICE"/></intent-filter><meta-data android:name="android.nfc.cardemulation.host_apdu_service" android:resource="@xml/card"/></service></application></manifest>''')
(p/'res/xml/card.xml').write_text('''<host-apdu-service xmlns:android="http://schemas.android.com/apk/res/android" android:description="@string/app_name" android:requireDeviceUnlock="false"><aid-group android:category="other" android:description="@string/app_name"><aid-filter android:name="F0010203040506"/></aid-group></host-apdu-service>''')
(p/'res/values').mkdir(exist_ok=True)
(p/'res/values/strings.xml').write_text('<resources><string name="app_name">NFC Diagnostic</string></resources>')
(p/'src/lab/nfc/Main.java').write_text('''package lab.nfc;
import android.app.*;import android.os.*;import android.nfc.*;import android.nfc.tech.*;import android.widget.*;import android.util.Log;
public class Main extends Activity implements NfcAdapter.ReaderCallback {
boolean payment=true;
TextView text; NfcAdapter n; public void onCreate(Bundle b){super.onCreate(b);getWindow().addFlags(128);n=NfcAdapter.getDefaultAdapter(this);LinearLayout l=new LinearLayout(this);l.setOrientation(1);text=new TextView(this);text.setTextSize(22);l.addView(text);Button r=new Button(this);r.setText("Reader mode");r.setOnClickListener(v->reader());l.addView(r);Button test=new Button(this);test.setText("Read diagnostic test card");test.setOnClickListener(v->{payment=false;reader();});l.addView(test);Button pay=new Button(this);pay.setText("Payment discovery only");pay.setOnClickListener(v->{payment=true;reader();});l.addView(pay);Button c=new Button(this);c.setText("Test card mode");c.setOnClickListener(v->card());l.addView(c);setContentView(l);}
protected void onResume(){super.onResume();if("reader".equals(getIntent().getStringExtra("mode")))reader();else card();}
void reader(){text.setText((payment?"PAYMENT DISCOVERY: waiting...":"TEST READER: waiting..."));n.enableReaderMode(this,this, NfcAdapter.FLAG_READER_NFC_A|NfcAdapter.FLAG_READER_NFC_B|NfcAdapter.FLAG_READER_SKIP_NDEF_CHECK,null);Log.i("NFCLab","READER_READY");}
void card(){n.disableReaderMode(this);text.setText("TEST CARD: ready for other phone");Log.i("NFCLab","CARD_READY");}
public void onTagDiscovered(Tag t){Log.i("NFCLab","TAG_DETECTED "+java.util.Arrays.toString(t.getTechList()));try{IsoDep d=IsoDep.get(t);if(d==null){Log.i("NFCLab","NON_ISODEP_TAG");return;}d.connect();d.setTimeout(3000);byte[] a=d.transceive(payment?new byte[]{0,(byte)0xA4,4,0,14,50,80,65,89,46,83,89,83,46,68,68,70,48,49,0}:new byte[]{0,(byte)0xA4,4,0,7,(byte)0xF0,1,2,3,4,5,6,0});String s=(payment?"PPSE bytes=":"TEST bytes=")+a.length+" status="+(a.length>=2?String.format("%02X%02X",a[a.length-2]&255,a[a.length-1]&255):"short");Log.i("NFCLab",s);runOnUiThread(()->text.setText("NFC exchange received: "+s));d.close();}catch(Exception e){Log.e("NFCLab","EXCHANGE_FAILED",e);}}
}''')
(p/'src/lab/nfc/Card.java').write_text('''package lab.nfc;import android.nfc.cardemulation.HostApduService;import android.os.Bundle;import android.util.Log; public class Card extends HostApduService {public byte[] processCommandApdu(byte[] a,Bundle b){Log.i("NFCLab","CARD_APDU_RECEIVED bytes="+a.length);return new byte[]{78,70,67,95,79,75,(byte)0x90,0};}public void onDeactivated(int reason){Log.i("NFCLab","CARD_DEACTIVATED "+reason);}}''')
run('javac','-source','8','-target','8','-classpath',jar,'-d','classes',*list((p/'src/lab/nfc').glob('*.java')))
run(bt/'d8.bat','--lib',jar,'--output','dex',*list((p/'classes/lab/nfc').glob('*.class')))
run(bt/'aapt2.exe','compile','--dir','res','-o','res.zip')
run(bt/'aapt2.exe','link','-o','unsigned.apk','--manifest','AndroidManifest.xml','-I',jar,'res.zip')
run('jar','uf','unsigned.apk','-C','dex','classes.dex')
run(bt/'zipalign.exe','-f','4','unsigned.apk','aligned.apk')
if not (p/'test.keystore').exists():run('keytool','-genkeypair','-keystore','test.keystore','-storepass','android','-keypass','android','-alias','test','-dname','CN=Local NFC Diagnostic','-keyalg','RSA','-validity','3650')
run(bt/'apksigner.bat','sign','--ks','test.keystore','--ks-pass','pass:android','--out','nfc-diagnostic.apk','aligned.apk')
